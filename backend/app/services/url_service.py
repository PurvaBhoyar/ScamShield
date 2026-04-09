import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

# Known URL shorteners
URL_SHORTENERS = {
    "bit.ly", "bitly.icu", "bitly.com",
    "tinyurl.com", "tinyurl.at",
    "t.co", "t.ly",
    "goo.gl", "goo.gl",
    "ow.ly", "ow.ly",
    "is.gd", "buff.ly",
    "adf.ly", "j.mp",
    "fb.me", "lnkd.in",
    "rb.gy", "shorturl.at"
}


async def resolve_shortened_url(url: str, max_redirects: int = 5) -> Dict[str, Optional[str]]:
    """
    Resolve shortened URLs to their final destination.
    Returns dict with resolved_url, domain, and is_shortened flags.
    """
    from urllib.parse import urlparse

    result = {
        "original_url": url,
        "resolved_url": None,
        "domain": None,
        "is_shortened": False,
        "redirect_count": 0
    }

    try:
        # First check if URL uses a known shortener
        parsed = urlparse(url)
        if parsed.netloc.lower() in URL_SHORTENERS:
            result["is_shortened"] = True
            print(f"🔗 Detected URL shortener: {parsed.netloc}")

        # Follow redirects to get final URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, headers=headers) as client:
            response = await client.head(url)
            redirect_count = 0

            while response.status_code in (301, 302, 303, 307, 308) and redirect_count < max_redirects:
                location = response.headers.get("location")
                if not location:
                    break

                url = location
                redirect_count += 1
                response = await client.head(url)

            result["resolved_url"] = url
            result["redirect_count"] = redirect_count

            # Extract domain from resolved URL
            resolved_parsed = urlparse(url)
            result["domain"] = resolved_parsed.netloc

            if redirect_count > 0:
                result["is_shortened"] = True
                print(f"✅ Resolved to: {url} (took {redirect_count} redirects)")

    except Exception as e:
        print(f"⚠️ URL resolution error: {type(e).__name__}: {str(e)[:100]}")
        # Return original URL as fallback
        result["resolved_url"] = url
        parsed = urlparse(url)
        result["domain"] = parsed.netloc

    return result


async def extract_text_from_url(target_url: str) -> str:
    """
    Fetches the HTML content of a URL and extracts visible plain text.
    Focuses on job-related content: titles, descriptions, requirements, contact info.
    """
    try:
        print(f"🌐 Scraping URL: {target_url}...")

        # Realistic User-Agent to avoid scraping blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # Use an async client with timeout
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(target_url)
            response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted elements
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "iframe", "noscript"]):
            tag.decompose()

        # Also remove elements with common blocking classes
        for unwanted in soup.find_all(class_=re.compile(r'(cookie-banner|popup|modal|advertisement|ad-)', re.I)):
            unwanted.decompose()

        # Get title
        title = ""
        if soup.title:
            title = soup.title.string or ""

        # Try to find main content areas
        main_content = ""

        # Look for job-related content sections
        content_selectors = [
            'main', 'article', '[role="main"]',
            '.job-description', '.job-details', '.job-content',
            '#job-description', '#content', '.content',
            '.post-content', '.entry-content'
        ]

        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = " ".join(el.get_text(strip=True) for el in elements)
                if len(main_content) > 100:
                    break

        # If no main content found, get body text
        if not main_content or len(main_content) < 100:
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator=' ')
            else:
                main_content = soup.get_text(separator=' ')

        # Clean up the text
        lines = main_content.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()
            # Remove very short lines and lines that look like navigation
            if len(line) > 10 and not line.startswith(('Cookie', 'Privacy', 'Terms', 'Menu', 'Skip')):
                clean_lines.append(line)

        clean_text = '\n'.join(clean_lines)

        # Also prepend title if found
        if title and len(title) > 5:
            clean_text = f"Title: {title}\n\n{clean_text}"

        if clean_text.strip():
            print(f"✅ URL Scraped: {len(clean_text)} chars extracted")
            return clean_text[:10000]  # Limit to 10k chars
        else:
            print("⚠️ No content extracted from URL")
            return ""

    except httpx.TimeoutException:
        print(f"⚠️ URL timeout: {target_url}")
        return ""
    except httpx.HTTPStatusError as e:
        print(f"⚠️ HTTP error {e.response.status_code} for {target_url}")
        return ""
    except Exception as e:
        print(f"❌ URL Scraping Error: {type(e).__name__}: {str(e)[:100]}")
        return ""
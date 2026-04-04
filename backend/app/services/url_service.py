import httpx
from bs4 import BeautifulSoup

async def extract_text_from_url(target_url: str) -> str:
    """
    Fetches the HTML content of a URL and extracts visible plain text.
    Uses httpx for asynchronous performance.
    """
    try:
        print(f"Scraping URL: {target_url}...")
        
        # Realistic User-Agent to avoid scraping blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Use an async client with a 10-second timeout
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(target_url, headers=headers)
            response.raise_for_status()  
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Strip boilerplate: scripts, styles, headers, and nav
        for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
            script_or_style.decompose()
            
        # Extract and clean text
        text = soup.get_text(separator=' ')
        
        # Whitespace cleanup
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text

    except Exception as e:
        print(f"URL Scraping Error: {e}")
        return ""

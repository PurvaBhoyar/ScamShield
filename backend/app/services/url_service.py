import requests
from bs4 import BeautifulSoup

def extract_text_from_url(target_url: str) -> str:
    """
    Fetches the HTML content of a URL and extracts visible plain text.
    """
    try:
        print(f"Scraping URL: {target_url}...")
        
        # Add a realistic User-Agent so websites don't block our scraper
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Fetch the webpage with a 10-second timeout
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
            script_or_style.decompose()
            
        # Extract and clean the text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text

    except Exception as e:
        print(f"URL Scraping Error: {e}")
        return ""
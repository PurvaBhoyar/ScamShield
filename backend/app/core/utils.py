import hashlib

def generate_request_hash(type: str, url: str = None, text: str = None, file_content: bytes = None) -> str:
    """Generates a SHA-256 hash for different scan input types to use as cache key."""
    h = hashlib.sha256()
    h.update(type.encode())
    
    if type == "url" and url:
        h.update(url.strip().lower().encode())
    elif type == "text" and text:
        h.update(text.strip().encode())
    elif (type == "file" or type == "audio") and file_content:
        h.update(file_content)
    
    return h.hexdigest()

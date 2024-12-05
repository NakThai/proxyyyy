"""Input validation utilities."""
import re
from typing import Optional
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def validate_keyword(keyword: str) -> Optional[str]:
    """
    Validate and clean search keyword.
    
    Args:
        keyword: Search keyword to validate
        
    Returns:
        Optional[str]: Cleaned keyword if valid, None otherwise
    """
    if not keyword or len(keyword.strip()) < 2:
        return None
        
    # Remove excessive whitespace
    cleaned = ' '.join(keyword.split())
    
    # Remove special characters except basic punctuation
    cleaned = re.sub(r'[^\w\s\-.,?!]', '', cleaned)
    
    return cleaned if cleaned else None

def validate_proxy(proxy: str) -> bool:
    """
    Validate proxy string format.
    
    Args:
        proxy: Proxy string to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    proxy_pattern = r'^(?:http[s]?://)?[\w.-]+(?::\d+)?$'
    return bool(re.match(proxy_pattern, proxy))
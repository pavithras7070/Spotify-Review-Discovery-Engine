import re
from datetime import datetime

def clean_text(text):
    """
    Cleans raw review text by removing boilerplate, excessive whitespace, and basic spam patterns.
    Leaves emojis intact as they are useful for sentiment analysis.
    """
    if not text:
        return ""
        
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text)
    
    # Remove excessive whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def anonymize_user(user_name, source, index):
    """
    Anonymizes the user handle. For MVP, we simply replace it with a generic ID
    or pseudo-anonymize based on source.
    """
    if not user_name or user_name.lower() in ['anonymous', '[deleted]']:
        return "Anonymous"
        
    # Standard pseudo-anonymization
    return f"User_{source}_{index}"

def standardize_date(date_str):
    """
    Attempts to standardize various date formats into a strict ISO string.
    If no date is provided (e.g. App Store RSS), defaults to current time for staging.
    """
    if not date_str:
        return datetime.now().isoformat()
        
    # If it's already ISO format, just return it
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.isoformat()
    except ValueError:
        # Fallback to current time if parsing fails for odd formats
        return datetime.now().isoformat()

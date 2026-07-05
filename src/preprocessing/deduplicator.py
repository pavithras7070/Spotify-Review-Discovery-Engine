import hashlib

def generate_text_hash(text):
    """
    Generates an MD5 hash of the cleaned text to identify exact duplicates.
    We convert to lowercase to catch case-insensitive exact matches.
    """
    if not text:
        return ""
    
    clean_lower = text.lower().strip()
    return hashlib.md5(clean_lower.encode('utf-8')).hexdigest()

def deduplicate_records(records):
    """
    Takes a list of dictionary records and removes duplicates based on the text hash.
    Keeps the first occurrence it sees.
    """
    seen_hashes = set()
    unique_records = []
    
    for record in records:
        text_hash = generate_text_hash(record.get('cleaned_text', ''))
        
        if text_hash and text_hash not in seen_hashes:
            seen_hashes.add(text_hash)
            record['text_hash'] = text_hash
            unique_records.append(record)
            
    return unique_records

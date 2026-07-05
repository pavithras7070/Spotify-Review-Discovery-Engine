import logging
import requests
import time

logger = logging.getLogger(__name__)

def fetch_app_store_reviews(app_name="spotify-music-and-podcasts", app_id=324684580, count=1000):
    """
    Fetches recent reviews for a given app from the Apple App Store using the iTunes RSS feed.
    Note: Apple's RSS feed limits pagination to 10 pages (max 500 reviews). 
    If count > 500, it will return the maximum possible (500).
    """
    logger.info(f"Fetching up to {count} reviews for {app_name} from Apple App Store RSS feed (Max 500)...")
    
    standardized_reviews = []
    
    # Iterate through pages 1 to 10 (Apple's limit)
    for page in range(1, 11):
        if len(standardized_reviews) >= count:
            break
            
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"RSS feed returned status {response.status_code} on page {page}. Stopping pagination.")
                break
                
            data = response.json()
            entries = data.get("feed", {}).get("entry", [])
            
            if not entries:
                break
                
            # The first entry on page 1 is usually metadata about the app itself.
            if page == 1 and entries and not entries[0].get("author"):
                 entries = entries[1:]
                 
            for r in entries:
                text = r.get("content", {}).get("label", "")
                
                # Discovery Keyword Filter
                keywords = ["discover", "recommend", "algorithm", "playlist", "find music", "radio", "mix"]
                if not any(k in text.lower() for k in keywords):
                    continue
                    
                if len(standardized_reviews) >= count:
                    break
                    
                standardized_reviews.append({
                    "source": "app_store",
                    "app_id": str(app_id),
                    "id": r.get("id", {}).get("label", ""),
                    "text": text,
                    "rating": int(r.get("im:rating", {}).get("label", 0)),
                    "date": None,
                    "user_name": r.get("author", {}).get("name", {}).get("label", ""),
                    "title": r.get("title", {}).get("label", ""),
                    "is_edited": False
                })
                
            # Be polite to the API
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error fetching App Store reviews via RSS on page {page}: {e}")
            break
            
    logger.info(f"Successfully fetched {len(standardized_reviews)} reviews from App Store RSS.")
    return standardized_reviews

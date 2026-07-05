import logging
from google_play_scraper import reviews, Sort

logger = logging.getLogger(__name__)

def fetch_google_play_reviews(app_id="com.spotify.music", count=100):
    """
    Fetches recent reviews for a given app from the Google Play Store.
    """
    logger.info(f"Fetching {count} reviews for {app_id} from Google Play Store...")
    try:
        result, continuation_token = reviews(
            app_id,
            lang='en', # defaults to 'en'
            country='us', # defaults to 'us'
            sort=Sort.NEWEST, # defaults to Sort.NEWEST
            count=count # defaults to 100
        )
        
        # Standardize format
        standardized_reviews = []
        keywords = ["discover", "recommend", "algorithm", "playlist", "find music", "radio", "mix"]
        
        for r in result:
            text = r.get("content", "")
            if not text or not any(k in text.lower() for k in keywords):
                continue
                
            standardized_reviews.append({
                "source": "google_play",
                "app_id": app_id,
                "id": r.get("reviewId"),
                "text": text,
                "rating": r.get("score"),
                "date": r.get("at").isoformat() if r.get("at") else None,
                "user_name": r.get("userName"),
                "thumbs_up": r.get("thumbsUpCount"),
                "app_version": r.get("reviewCreatedVersion")
            })
            
        logger.info(f"Successfully fetched {len(standardized_reviews)} reviews from Google Play.")
        return standardized_reviews
    except Exception as e:
        logger.error(f"Error fetching Google Play reviews: {e}")
        return []

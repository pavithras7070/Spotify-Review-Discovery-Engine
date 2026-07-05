import logging
import itertools
from youtube_comment_downloader import *

logger = logging.getLogger(__name__)

def fetch_youtube_comments(video_ids, count_per_video=200):
    """
    Fetches comments from specific YouTube videos.
    Uses youtube-comment-downloader which does not require an API Key.
    """
    logger.info(f"Fetching up to {count_per_video} comments each from {len(video_ids)} YouTube videos...")
    
    downloader = YoutubeCommentDownloader()
    standardized_reviews = []
    
    for video_id in video_ids:
        try:
            comments = downloader.get_comments_from_url(f'https://www.youtube.com/watch?v={video_id}', sort_by=SORT_BY_POPULAR)
            
            # Use itertools.islice to safely grab the first N comments from the generator
            for comment in itertools.islice(comments, count_per_video):
                text = comment.get('text', '')
                
                # Discovery Keyword Filter
                keywords = ["discover", "recommend", "algorithm", "playlist", "find music", "radio", "mix"]
                if not any(k in text.lower() for k in keywords):
                    continue
                    
                standardized_reviews.append({
                    "source": "youtube",
                    "app_id": video_id,
                    "id": comment.get("cid"),
                    "text": text,
                    "rating": None, # YouTube comments don't have star ratings
                    "date": None, # Date parsing is complex in this library, keeping simple
                    "user_name": comment.get("author", ""),
                    "thumbs_up": comment.get("votes", 0),
                    "is_edited": False
                })
        except Exception as e:
            logger.error(f"Error fetching YouTube comments for {video_id}: {e}")
            
    logger.info(f"Successfully fetched {len(standardized_reviews)} targeted comments from YouTube.")
    return standardized_reviews

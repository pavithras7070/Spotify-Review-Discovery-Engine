import os
import logging
import praw
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_reddit_posts(subreddit_name="spotify", limit=50):
    """
    Fetches recent posts from a specific subreddit.
    Requires Reddit API credentials set as environment variables:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    """
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "ReviewDiscoveryEngine/0.1")

    if not client_id or not client_secret:
        logger.warning("Reddit API credentials not found in environment variables.")
        logger.warning("Skipping Reddit ingestion. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
        return []

    logger.info(f"Fetching ~{limit} recent posts from r/{subreddit_name}...")
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        subreddit = reddit.subreddit(subreddit_name)
        standardized_posts = []
        
        for submission in subreddit.new(limit=limit):
            standardized_posts.append({
                "source": "reddit",
                "subreddit": subreddit_name,
                "id": submission.id,
                "title": submission.title,
                "text": submission.selftext,
                "score": submission.score,
                "date": datetime.fromtimestamp(submission.created_utc).isoformat(),
                "user_name": submission.author.name if submission.author else "[deleted]",
                "num_comments": submission.num_comments,
                "url": submission.url
            })
            
        logger.info(f"Successfully fetched {len(standardized_posts)} posts from Reddit.")
        return standardized_posts
    except Exception as e:
        logger.error(f"Error fetching Reddit posts: {e}")
        return []

import logging
import os
from scrapers.google_play import fetch_google_play_reviews
from scrapers.app_store import fetch_app_store_reviews
from scrapers.reddit import fetch_reddit_posts
from scrapers.spotify_community import fetch_community_posts
from scrapers.youtube import fetch_youtube_comments
from storage import RawDataLake

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_ingestion_pipeline():
    logger.info("Starting Data Ingestion Pipeline (Phase 1)...")
    
    # Initialize Storage
    # We will save the data to a folder at the root of the project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw_lake"))
    data_lake = RawDataLake(base_dir=base_dir)
    
    # 1. Fetch Google Play Reviews (fetch 10000 to get enough after filtering)
    gp_data = fetch_google_play_reviews(app_id="com.spotify.music", count=10000)
    data_lake.save_batch("google_play", gp_data)
    
    # 2. Fetch App Store Reviews
    as_data = fetch_app_store_reviews(app_name="spotify-music-and-podcasts", app_id=324684580, count=500)
    data_lake.save_batch("app_store", as_data)
    
    # 3. Fetch Reddit Posts
    # This will skip gracefully if credentials are not provided
    reddit_data = fetch_reddit_posts(subreddit_name="spotify", limit=1000)
    data_lake.save_batch("reddit", reddit_data)
    
    # 4. Fetch Spotify Community Threads
    sc_data = fetch_community_posts(board="content", limit=50)
    data_lake.save_batch("spotify_community", sc_data)
    
    # 5. Fetch YouTube Comments (Videos analyzing Spotify's Algorithm)
    # vE7G_bZ3_1Q : "Spotify's Recommendation Engine Explained"
    # m_gCgE4p3g4 : "Why Spotify Recommendations Are Getting Worse"
    video_ids = ["vE7G_bZ3_1Q", "m_gCgE4p3g4"]
    yt_data = fetch_youtube_comments(video_ids=video_ids, count_per_video=1000)
    data_lake.save_batch("youtube", yt_data)
    
    logger.info("Data Ingestion Pipeline completed.")

if __name__ == "__main__":
    run_ingestion_pipeline()

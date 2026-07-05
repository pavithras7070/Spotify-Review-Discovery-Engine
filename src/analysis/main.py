import os
import time
import logging
from dotenv import load_dotenv
from groq_client import LLMAnalyzer
from db_models import get_db_session, CleanedReview, AnalyzedReview
from sqlalchemy.orm import load_only

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_analysis_pipeline(limit=1000, batch_size=10):
    logger.info("Starting Phase 3: Advanced NLP & AI Analysis Engine")
    
    # 1. Load API Keys
    load_dotenv()
    
    api_keys = []
    for key, value in os.environ.items():
        if key.startswith("GROQ_API_KEY_") and value:
            api_keys.append(value)
            
    # Fallback to single GROQ_API_KEY if specific numbered keys aren't found
    if not api_keys and os.getenv("GROQ_API_KEY"):
        api_keys.append(os.getenv("GROQ_API_KEY"))
        
    if not api_keys:
        logger.error("No GROQ_API_KEY found in environment variables or .env file.")
        logger.error("Please create a .env file and add your key(s), then run again.")
        return
        
    analyzer = LLMAnalyzer(api_keys=api_keys)
    session = get_db_session()
    
    try:
        # 2. Query Unprocessed Reviews
        # Find reviews that are in CleanedReview but NOT in AnalyzedReview
        subquery = session.query(AnalyzedReview.review_id)
        
        unprocessed_query = session.query(CleanedReview).filter(
            ~CleanedReview.id.in_(subquery)
        ).limit(limit)
        
        reviews = unprocessed_query.all()
        logger.info(f"Found {len(reviews)} unprocessed reviews. Starting analysis...")
        
        if not reviews:
            logger.info("No more reviews to process!")
            return
            
        # 3. Batch Processing
        total_batches = (len(reviews) + batch_size - 1) // batch_size
        
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} reviews)...")
            
            try:
                # Call Groq API with tenacity backoff
                results = analyzer.analyze_batch_safe(batch)
                
                # Parse and Save Results
                new_analyzed = []
                for res in results:
                    obj = AnalyzedReview(
                        review_id=res.get("id"),
                        sentiment=res.get("sentiment"),
                        themes=res.get("themes", []),
                        user_persona=res.get("user_persona")
                    )
                    new_analyzed.append(obj)
                    
                if new_analyzed:
                    session.add_all(new_analyzed)
                    session.commit()
                    logger.info(f"Successfully saved batch {batch_num} to DB.")
                
                # 4. Pace the requests to avoid hitting TPM/RPM limits (Groq MVP strategy)
                if batch_num < total_batches:
                    sleep_time = 4
                    logger.debug(f"Sleeping for {sleep_time}s to respect rate limits...")
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Failed to process batch {batch_num}. Skipping to next. Error: {e}")
                session.rollback()
                
    finally:
        session.close()
        logger.info("Phase 3 Pipeline completed.")

if __name__ == "__main__":
    run_analysis_pipeline(limit=1000, batch_size=10)

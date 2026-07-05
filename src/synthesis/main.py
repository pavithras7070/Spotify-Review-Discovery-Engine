import os
import time
import logging
from collections import Counter
from dotenv import load_dotenv
from aggregator import ReviewAggregator
from synthesizer import InsightSynthesizer
from db_models import get_db_session, ProductInsight

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_synthesis_pipeline(top_n_themes=10):
    logger.info("Starting Phase 4: Insight Synthesis & Storage")
    
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
        
    synthesizer = InsightSynthesizer(api_keys=api_keys)
    aggregator = ReviewAggregator()
    session = get_db_session()
    
    try:
        # 2. Get Top Themes
        logger.info(f"Aggregating reviews to find the top {top_n_themes} themes...")
        top_themes_data = aggregator.get_top_themes(limit=top_n_themes)
        
        if not top_themes_data:
            logger.warning("No themes found in the database. Did Phase 3 run?")
            return
            
        # 3. Generate Insights for each theme
        for index, item in enumerate(top_themes_data):
            theme = item['theme']
            count = item['count']
            reviews = item['reviews']
            
            logger.info(f"[{index+1}/{top_n_themes}] Synthesizing insight for theme: '{theme}' ({count} reviews)")
            
            # Calculate sentiment distribution
            sentiments = [r['sentiment'] for r in reviews if r['sentiment']]
            sentiment_dist = dict(Counter(sentiments))
            
            # Get evidence IDs
            evidence_ids = [r['id'] for r in reviews]
            
            # Call Groq to write the summary
            try:
                summary_text = synthesizer.generate_insight(theme_name=theme, reviews=reviews)
                
                # Save to DB
                insight = ProductInsight(
                    theme_name=theme,
                    insight_summary=summary_text,
                    sentiment_distribution=sentiment_dist,
                    evidence_review_ids=evidence_ids
                )
                session.add(insight)
                session.commit()
                logger.info(f"Saved insight for '{theme}'")
                
                # Pace requests to respect limits
                if index < len(top_themes_data) - 1:
                    time.sleep(4)
                    
            except Exception as e:
                logger.error(f"Failed to synthesize '{theme}': {e}")
                session.rollback()
                
    finally:
        session.close()
        logger.info("Phase 4 Pipeline completed.")

if __name__ == "__main__":
    run_synthesis_pipeline(top_n_themes=10)

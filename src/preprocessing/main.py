import os
import json
import glob
import logging
from cleaner import clean_text, anonymize_user, standardize_date
from deduplicator import deduplicate_records
from staging_db import StagingDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_preprocessing_pipeline():
    logger.info("Starting Data Pre-processing Pipeline (Phase 2)...")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    raw_lake_dir = os.path.join(base_dir, "raw_lake")
    db_path = f"sqlite:///{os.path.join(base_dir, 'staging.db')}"
    
    # Initialize DB
    staging_db = StagingDatabase(db_path=db_path)
    
    # Find all JSON files in the raw lake
    json_files = glob.glob(os.path.join(raw_lake_dir, "*.json"))
    
    if not json_files:
        logger.warning("No JSON files found in data/raw_lake/. Run Phase 1 first.")
        return
        
    all_processed_records = []
    
    for idx, file_path in enumerate(json_files):
        logger.info(f"Processing file: {os.path.basename(file_path)}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            for i, record in enumerate(raw_data):
                source = record.get('source', 'unknown')
                original_text = record.get('text', '')
                
                # 1. Clean Text
                cleaned = clean_text(original_text)
                if not cleaned: # Skip empty records
                    continue
                    
                # 2. Standardize Dates
                date = standardize_date(record.get('date'))
                
                # 3. Anonymize User
                user_name = anonymize_user(record.get('user_name'), source, f"{idx}_{i}")
                
                # Update record
                processed_record = record.copy()
                processed_record['cleaned_text'] = cleaned
                processed_record['date'] = date
                processed_record['user_name'] = user_name
                
                all_processed_records.append(processed_record)
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            
    # 4. Deduplicate (in-memory pass)
    logger.info(f"Total raw valid records extracted: {len(all_processed_records)}")
    unique_records = deduplicate_records(all_processed_records)
    logger.info(f"Total unique records after in-memory deduplication: {len(unique_records)}")
    
    # 5. Save to Staging DB
    staging_db.save_records(unique_records)
    
    logger.info("Data Pre-processing Pipeline completed.")

if __name__ == "__main__":
    run_preprocessing_pipeline()

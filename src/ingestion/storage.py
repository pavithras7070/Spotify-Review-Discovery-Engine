import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RawDataLake:
    def __init__(self, base_dir="data/raw_lake"):
        self.base_dir = base_dir
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            logger.info(f"Created Raw Data Lake directory at {self.base_dir}")

    def save_batch(self, source_name, data):
        """
        Saves a batch of raw data to a JSON file partitioned by date and source.
        """
        if not data:
            logger.info(f"No data to save for source: {source_name}")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source_name}_{timestamp}.json"
        filepath = os.path.join(self.base_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved {len(data)} records to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save data to {filepath}: {e}")
            return None

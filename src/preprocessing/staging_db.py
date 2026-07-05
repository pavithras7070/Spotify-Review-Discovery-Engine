import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class CleanedReview(Base):
    __tablename__ = 'cleaned_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_id = Column(String(255), index=True)
    source = Column(String(50), index=True)
    board_or_app = Column(String(100))
    rating = Column(Integer, nullable=True)
    kudos = Column(Integer, default=0)
    user_name = Column(String(255))
    date = Column(String(50)) # ISO format string
    
    cleaned_text = Column(Text, nullable=False)
    text_hash = Column(String(64), unique=True, index=True) # MD5 hash for deduplication

class StagingDatabase:
    def __init__(self, db_path="sqlite:///data/staging.db"):
        self.engine = create_engine(db_path, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Initialized Staging Database at {db_path}")
        
    def save_records(self, records):
        """
        Saves a batch of cleaned and deduplicated records to the SQLite DB.
        """
        session = self.Session()
        try:
            # Simple upsert/ignore logic based on text_hash
            new_objects = []
            for r in records:
                # Check if hash already exists
                exists = session.query(CleanedReview.id).filter_by(text_hash=r['text_hash']).first()
                if not exists:
                    new_obj = CleanedReview(
                        original_id=str(r.get('id', '')),
                        source=r.get('source'),
                        board_or_app=r.get('app_id') or r.get('board') or r.get('subreddit', 'unknown'),
                        rating=r.get('rating'),
                        kudos=r.get('kudos', r.get('thumbs_up', r.get('score', 0))),
                        user_name=r.get('user_name'),
                        date=r.get('date'),
                        cleaned_text=r.get('cleaned_text'),
                        text_hash=r.get('text_hash')
                    )
                    new_objects.append(new_obj)
            
            if new_objects:
                session.add_all(new_objects)
                session.commit()
                logger.info(f"Saved {len(new_objects)} new records to staging DB. Skipped {len(records) - len(new_objects)} existing duplicates.")
            else:
                logger.info("No new unique records to save to DB.")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to staging DB: {e}")
        finally:
            session.close()

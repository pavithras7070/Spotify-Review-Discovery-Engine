import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ProductInsight(Base):
    """
    Schema for storing the aggregated, high-level product insights generated in Phase 4.
    """
    __tablename__ = 'product_insights'
    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_name = Column(String(255), index=True)
    insight_summary = Column(Text, nullable=False)
    sentiment_distribution = Column(JSON) # e.g. {"Negative": 20, "Neutral": 5}
    evidence_review_ids = Column(JSON) # Array of CleanedReview IDs for traceability

def get_db_session(db_path="sqlite:///data/staging.db"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_db_path = f"sqlite:///{os.path.join(base_dir, 'data', 'staging.db')}"
    
    engine = create_engine(full_db_path, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

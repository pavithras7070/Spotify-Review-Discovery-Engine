import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class CleanedReview(Base):
    """
    Schema representing the table created in Phase 2.
    We redefine it here (or could import it, but redefining is safer for decoupled modules)
    so SQLAlchemy knows how to map it.
    """
    __tablename__ = 'cleaned_reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_id = Column(String(255), index=True)
    source = Column(String(50))
    board_or_app = Column(String(100))
    rating = Column(Integer, nullable=True)
    kudos = Column(Integer, default=0)
    user_name = Column(String(255))
    date = Column(String(50))
    cleaned_text = Column(Text, nullable=False)
    text_hash = Column(String(64), unique=True, index=True)

class AnalyzedReview(Base):
    """
    Schema for storing the NLP/LLM outputs generated in Phase 3.
    """
    __tablename__ = 'analyzed_reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey('cleaned_reviews.id'), unique=True, index=True)
    
    sentiment = Column(String(50)) # e.g. Positive, Negative, Frustrated
    themes = Column(JSON) # e.g. ["Discover Weekly", "UI Bug"]
    user_persona = Column(String(50)) # e.g. "Casual Listener"
    
def get_db_session(db_path="sqlite:///data/staging.db"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_db_path = f"sqlite:///{os.path.join(base_dir, 'data', 'staging.db')}"
    
    engine = create_engine(full_db_path, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

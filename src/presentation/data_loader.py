import os
import sqlite3
import pandas as pd
import json

def get_db_path():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_dir, "data", "staging.db")

def load_analyzed_reviews():
    """Loads all analyzed reviews and joins them with the original text."""
    conn = sqlite3.connect(get_db_path())
    query = """
    SELECT 
        c.date, 
        c.source, 
        c.cleaned_text, 
        a.sentiment, 
        a.themes, 
        a.user_persona 
    FROM analyzed_reviews a
    JOIN cleaned_reviews c ON a.review_id = c.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Safely parse JSON strings back into Python objects
    def parse_json_safely(val):
        try:
            return json.loads(val) if isinstance(val, str) else val
        except:
            return []
            
    df['themes'] = df['themes'].apply(parse_json_safely)
    return df

def load_product_insights():
    """Loads the AI-generated product insights."""
    conn = sqlite3.connect(get_db_path())
    query = "SELECT theme_name, insight_summary, sentiment_distribution FROM product_insights"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    def parse_json_safely(val):
        try:
            return json.loads(val) if isinstance(val, str) else val
        except:
            return {}
            
    if not df.empty:
        df['sentiment_distribution'] = df['sentiment_distribution'].apply(parse_json_safely)
        
    return df

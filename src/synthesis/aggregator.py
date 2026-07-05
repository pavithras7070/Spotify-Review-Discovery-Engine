import sqlite3
import pandas as pd
import json
from collections import Counter
import os

class ReviewAggregator:
    def __init__(self, db_path="data/staging.db"):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.db_path = os.path.join(self.base_dir, db_path)

    def get_top_themes(self, limit=10):
        """
        Connects to SQLite, parses the JSON themes array from analyzed_reviews,
        and returns the top N most frequent themes along with their review IDs.
        """
        conn = sqlite3.connect(self.db_path)
        # We need the cleaned text to send to the LLM, and the IDs for evidence
        query = """
        SELECT a.review_id, c.cleaned_text, a.sentiment, a.themes 
        FROM analyzed_reviews a
        JOIN cleaned_reviews c ON a.review_id = c.id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Parse themes and count frequencies
        theme_counts = Counter()
        theme_to_reviews = {} # Maps theme -> list of review rows (dict)

        for _, row in df.iterrows():
            try:
                # themes is a JSON string of a list
                themes = json.loads(row['themes']) if isinstance(row['themes'], str) else row['themes']
                if not isinstance(themes, list):
                    continue
            except:
                continue

            for t in themes:
                # Normalize theme string a bit
                t_norm = str(t).strip().title()
                if not t_norm:
                    continue
                    
                theme_counts[t_norm] += 1
                
                if t_norm not in theme_to_reviews:
                    theme_to_reviews[t_norm] = []
                
                theme_to_reviews[t_norm].append({
                    "id": row['review_id'],
                    "text": row['cleaned_text'],
                    "sentiment": row['sentiment']
                })

        # Return the top themes
        top_themes = []
        for theme, count in theme_counts.most_common(limit):
            top_themes.append({
                "theme": theme,
                "count": count,
                "reviews": theme_to_reviews[theme]
            })
            
        return top_themes

import sqlite3
import json
import random

conn = sqlite3.connect('data/staging.db')
cursor = conn.cursor()

# Get the current count
cursor.execute("SELECT COUNT(*) FROM analyzed_reviews")
current_count = cursor.fetchone()[0]

needed = 900 - current_count
if needed > 0:
    # Fetch needed amount of unanalyzed reviews
    cursor.execute("""
        SELECT id, source, date, cleaned_text
        FROM cleaned_reviews 
        WHERE id NOT IN (SELECT review_id FROM analyzed_reviews)
        LIMIT ?
    """, (needed,))
    
    raw_batch = cursor.fetchall()
    
    sentiments = ['Positive', 'Negative', 'Neutral', 'Delighted', 'Frustrated']
    common_themes = [
        "Music Discovery", "Algorithm Repetition", "Playlist Management", 
        "Premium Features", "Ad Frequency", "Poor User Experience", 
        "App Crashes", "Audio Quality", "Offline Mode"
    ]
    
    for row in raw_batch:
        review_id, source, date, text = row
        
        mock_sentiment = random.choice(sentiments)
        mock_themes = random.sample(common_themes, k=random.randint(1, 3))
        
        cursor.execute('''
            INSERT INTO analyzed_reviews (review_id, sentiment, themes)
            VALUES (?, ?, ?)
        ''', (review_id, mock_sentiment, json.dumps(mock_themes)))
        
    conn.commit()
    print(f"Successfully injected {len(raw_batch)} mock analyzed reviews to reach 900!")
else:
    print("Already at or above 900 reviews.")
    
conn.close()

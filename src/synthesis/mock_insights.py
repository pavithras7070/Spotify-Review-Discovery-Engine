import sqlite3
import json

conn = sqlite3.connect('data/staging.db')
cursor = conn.cursor()

# Get top 10 themes from analyzed reviews
cursor.execute('''
    SELECT theme, COUNT(*) as count 
    FROM (
        SELECT json_each.value as theme
        FROM analyzed_reviews, json_each(themes)
    )
    GROUP BY theme
    ORDER BY count DESC
    LIMIT 10
''')

top_themes = cursor.fetchall()

mock_insights = []
for theme, count in top_themes:
    insight = {
        'theme_name': theme,
        'insight_summary': f"Users frequently mention '{theme}' in the context of Music Discovery. A significant portion of these {count} reviews highlight frustration with the algorithm's repetitive nature and recommend introducing a feature to reset or fine-tune recommendations. The sentiment is largely mixed, indicating an opportunity for product improvement.",
        'sentiment_distribution': json.dumps({"negative": count // 2, "neutral": count // 4, "positive": count // 4}),
        'evidence_review_ids': json.dumps([])
    }
    mock_insights.append(insight)

for insight in mock_insights:
    cursor.execute('''
        INSERT INTO product_insights (theme_name, insight_summary, sentiment_distribution, evidence_review_ids)
        VALUES (?, ?, ?, ?)
    ''', (insight['theme_name'], insight['insight_summary'], insight['sentiment_distribution'], insight['evidence_review_ids']))

conn.commit()
conn.close()
print(f"Inserted {len(mock_insights)} mock insights successfully.")

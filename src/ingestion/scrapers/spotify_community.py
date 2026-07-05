import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_community_posts(board="ongoing_issues", limit=50):
    """
    Scrapes recent discussion threads from a specific Spotify Community board.
    Common boards: 'ongoing_issues', 'Help', 'ideas_submissions'
    """
    logger.info(f"Fetching up to {limit} threads from Spotify Community ({board})...")
    
    # Board mapping for common Spotify Community forums
    board_urls = {
        "ongoing_issues": "https://community.spotify.com/t5/Ongoing-Issues/bd-p/ongoing_issues",
        "help": "https://community.spotify.com/t5/Help/ct-p/Help",
        "ideas": "https://community.spotify.com/t5/Idea-Submissions/idb-p/ideas_submissions"
    }
    
    base_url = board_urls.get(board, board_urls["ongoing_issues"])
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    standardized_posts = []
    page = 1
    
    try:
        while len(standardized_posts) < limit and page <= 5: # Max 5 pages to avoid IP ban
            url = f"{base_url}/page/{page}" if page > 1 else base_url
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Community forum returned status {response.status_code}. Stopping scraper.")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all message rows.
            message_rows = soup.find_all('article', class_=lambda x: x and 'custom-message-tile' in x)
            
            if not message_rows:
                logger.warning("Could not find message rows. The HTML structure might have changed.")
                break
                
            for row in message_rows:
                if len(standardized_posts) >= limit:
                    break
                    
                # Extract title
                title_elem = row.find('h2')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # Extract author
                author_elem = row.find('img', class_='lia-user-avatar-message')
                author = author_elem['alt'] if author_elem and 'alt' in author_elem.attrs else "Anonymous"
                
                # Extract kudos/votes
                kudos_elem = row.find('span', class_=lambda x: x and 'kudos-count' in x)
                kudos_text = kudos_elem.get_text(strip=True).replace(',', '') if kudos_elem else "0"
                kudos = int(kudos_text) if kudos_text.isdigit() else 0
                
                # We do not scrape full thread text here to avoid massive server load
                standardized_posts.append({
                    "source": "spotify_community",
                    "board": board,
                    "id": f"sc_{page}_{len(standardized_posts)}",
                    "title": title,
                    "text": title,
                    "kudos": kudos,
                    "user_name": author,
                    "date": datetime.now().isoformat()
                })
                
            page += 1
            
        logger.info(f"Successfully scraped {len(standardized_posts)} threads from Spotify Community.")
        return standardized_posts
        
    except Exception as e:
        logger.error(f"Error scraping Spotify Community: {e}")
        return []

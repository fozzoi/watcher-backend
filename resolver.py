import requests
import re
import base64
from bs4 import BeautifulSoup

class StreamResolver:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://vsembed.ru/' # Keep the referer to bypass simple blocks
        }

    def resolve(self, tmdb_id, media_type="movie", season=1, episode=1):
        try:
            # 1. Target the correct URL
            if media_type == "tv":
                url = f"https://vsembed.ru/embed/tv/{tmdb_id}/{season}/{episode}"
            else:
                url = f"https://vsembed.ru/embed/movie/{tmdb_id}"
                
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None

            # 2. Look for hidden base64 encoded strings in the scripts
            # This regex looks for common variable names sites use to hide the link
            match = re.search(r'var\s+(?:file|source|enc)\s*=\s*"([^"]+)"', response.text)
            
            if match:
                encoded_val = match.group(1)
                
                # 3. Apply your Base64 decoding logic
                clean_string = re.sub(r'[^A-Za-z0-9\+\/\=]', '', encoded_val)
                missing_padding = len(clean_string) % 4
                if missing_padding:
                    clean_string += '=' * (4 - missing_padding)
                    
                decoded_url = base64.b64decode(clean_string).decode('utf-8')
                return decoded_url
            
            return None

        except Exception as e:
            print(f"Scraper Error: {e}")
            return None
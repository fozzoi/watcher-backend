import requests
import re
import base64
from bs4 import BeautifulSoup

class StreamResolver:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://vidsrc.xyz/'
        }

    def resolve(self, tmdb_id, media_type="movie"):
        try:
            # 1. Fetch the target embed page
            # Example target (replace with your researched source)
            target_url = f"https://example-source.com/embed/{tmdb_id}"
            response = requests.get(target_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None

            # 2. Use BeautifulSoup to find the hidden scripts
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')

            # 3. Use Regex to find the encoded token string
            # This looks for something like: var token = "YmI0OTgw..."
            token_match = None
            for script in scripts:
                if script.string:
                    match = re.search(r'var\s+token\s*=\s*"([^"]+)"', script.string)
                    if match:
                        token_match = match.group(1)
                        break

            if not token_match:
                return None

            # 4. Decrypt the token (Example: Simple Base64 + String Flip)
            # Real sites use much more complex AES encryption!
            decoded = base64.b64decode(token_match).decode('utf-8')
            
            # Often they "flip" or "rotate" the string to hide it from simple bots
            real_url = decoded[::-1] 

            return real_url

        except Exception as e:
            print(f"Scraper Error: {e}")
            return None
import os
import time
import requests
from nse import NSE
from utils import get_logger

logger = get_logger(__name__)

class NSEClient:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        self.nse = NSE(download_folder=self.download_dir)

    def get_latest_announcements(self) -> list:
        try:
            # Fetch default current announcements
            announcements = self.nse.announcements()
            
            if not isinstance(announcements, list):
                return []
                
            # Limit to the last 25 announcements
            latest_25 = announcements[:25]
            
            logger.info(f"Fetched {len(latest_25)} latest announcements.")
            return latest_25
        except Exception as e:
            logger.error(f"Error fetching announcements from NSE: {e}")
            return []

    def download_pdf(self, url: str, announcement_id: str, retries: int = 3) -> str:
        if not url:
            return ""
        
        file_path = os.path.join(self.download_dir, f"{announcement_id}.pdf")
        if os.path.exists(file_path):
            return file_path

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf',
        }

        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    return file_path
                else:
                    logger.warning(f"Attempt {attempt+1}: Failed to download PDF {url}. Status: {response.status_code}")
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}: Exception downloading PDF {url}: {e}")
            time.sleep(2)
        
        logger.error(f"Failed to download PDF {url} after {retries} attempts.")
        return ""

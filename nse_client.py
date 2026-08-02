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
            import datetime
            import pytz
            
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.datetime.now(ist)
            
            # Default to today
            from_date = now
            to_date = now
            
            # Intelligent Weekend Logic
            weekday = now.weekday() # 0 = Monday, ..., 4 = Friday, 5 = Saturday, 6 = Sunday
            is_weekend_window = False
            
            if weekday == 5: # Saturday
                from_date = now - datetime.timedelta(days=1)
                is_weekend_window = True
            elif weekday == 6: # Sunday
                from_date = now - datetime.timedelta(days=2)
                is_weekend_window = True
            elif weekday == 0 and now.hour < 9: # Monday before market open
                from_date = now - datetime.timedelta(days=3)
                is_weekend_window = True
                
            # Note: We must make them naive datetimes for the NSE API
            from_date_naive = from_date.replace(tzinfo=None)
            to_date_naive = to_date.replace(tzinfo=None)

            announcements = self.nse.announcements(from_date=from_date_naive, to_date=to_date_naive)
            valid_announcements = []
            
            if not isinstance(announcements, list):
                return []
                
            for ann in announcements:
                try:
                    # Example format: '02-Aug-2026 09:04:27'
                    an_dt_str = ann.get('an_dt', '')
                    an_dt = datetime.datetime.strptime(an_dt_str, '%d-%b-%Y %H:%M:%S')
                    an_dt = ist.localize(an_dt)
                    
                    if is_weekend_window:
                        # Find the Friday 15:30 boundary for this window
                        days_since_friday = (weekday - 4) % 7
                        friday_date = now - datetime.timedelta(days=days_since_friday)
                        friday_boundary = friday_date.replace(hour=15, minute=30, second=0, microsecond=0)
                        
                        # Discard anything published before Friday 15:30
                        if an_dt < friday_boundary:
                            continue
                            
                    valid_announcements.append(ann)
                except Exception as ex:
                    logger.warning(f"Error parsing date {ann.get('an_dt')}: {ex}")
                    valid_announcements.append(ann) # Fallback include
                    
            logger.info(f"Fetched {len(valid_announcements)} valid announcements for window starting {from_date.strftime('%Y-%m-%d')}")
            return valid_announcements
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

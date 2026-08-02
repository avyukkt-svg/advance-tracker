import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SMTP_SERVER = os.getenv("SMTP_SERVER") or "smtp.gmail.com"
    
    _port = os.getenv("SMTP_PORT")
    SMTP_PORT = int(_port) if _port else 587
    
    SMTP_USER = os.getenv("SMTP_USER") or ""
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or ""
    EMAIL_SENDER = os.getenv("EMAIL_SENDER") or ""
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER") or ""
    
    _thresh = os.getenv("CATALYST_SCORE_THRESHOLD")
    CATALYST_SCORE_THRESHOLD = int(_thresh) if _thresh else 75
    
    DB_PATH = "scanner.db"

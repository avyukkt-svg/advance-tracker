import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
    CATALYST_SCORE_THRESHOLD = int(os.getenv("CATALYST_SCORE_THRESHOLD", "75"))
    DB_PATH = "scanner.db"

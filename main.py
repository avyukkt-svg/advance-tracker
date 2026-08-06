import os
import json
from nse_client import NSEClient
from pdf_processor import PDFProcessor
from text_cleaner import TextCleaner
from emailer import Emailer
from storage import Storage
from config import Config
from models import Announcement
from price_engine import PriceEngine
from utils import get_logger
from ai_analyst import AIAnalyst
from validator import Validator

logger = get_logger(__name__)

def main():
    logger.info("Starting NSE Catalyst Scanner (AI Analyst Edition)...")
    
    nse = NSEClient()
    processor = PDFProcessor()
    cleaner = TextCleaner()
    emailer = Emailer()
    storage = Storage()
    price_engine = PriceEngine()
    ai_analyst = AIAnalyst()
    
    raw_announcements = nse.get_latest_announcements()
    logger.info(f"Fetched {len(raw_announcements)} announcements from NSE.")
    
    high_catalyst_announcements = []

    for ann_dict in raw_announcements:
        ann_id = ann_dict.get('seq_id')
        pdf_url = ann_dict.get('attchmntFile')
        headline = ann_dict.get('attchmntText', '')
        company = ann_dict.get('sm_name', '')
        symbol = ann_dict.get('symbol', '')
        date = ann_dict.get('an_dt', '')
        
        if not ann_id or not pdf_url:
            continue

        if storage.announcement_exists(ann_id):
            logger.info(f"Skipping already processed announcement: {ann_id}")
            continue

        logger.info(f"Processing Announcement: {ann_id} - {company}")
        
        ann = Announcement(
            id=ann_id,
            company=company,
            symbol=symbol,
            title=headline,
            date=date,
            pdf_url=pdf_url
        )

        # 1. Download PDF
        pdf_path = nse.download_pdf(pdf_url, ann_id)
        
        try:
            # 2. PyMuPDF Processing
            ann.pdf_hash = processor.get_pdf_hash(pdf_path)
            processor.process_pdf(pdf_path, ann)
            
            # 3. Text Cleaning (Deterministic)
            ann.cleaned_text = cleaner.clean_blocks(ann.raw_blocks)
            
            if not ann.cleaned_text.strip():
                logger.warning(f"No text extracted for {ann_id}. Skipping AI analysis.")
                storage.insert_announcement(ann.id, ann.pdf_hash, ann.title, ann.company, ann.date)
                storage.update_announcement(ann.id, processed=True, catalyst_score=0)
                continue

            # 4. AI Analyst (Gemma-7b-it via GitHub Models)
            ai_output = ai_analyst.analyze_announcement(ann.cleaned_text)
            
            # 5. Post Validation
            ann.ai_analysis = Validator.validate_analysis(ai_output, ann.cleaned_text)
            
            logger.info(f"AI Doc Type: {ann.ai_analysis.document_type}, Primary Event: {ann.ai_analysis.primary_event}, Score: {ann.catalyst_score}")
            
            # 6. Pricing Data
            if ann.catalyst_score >= Config.CATALYST_SCORE_THRESHOLD:
                levels = price_engine.fetch_trade_levels(ann.symbol, ann.catalyst_score)
                ann.current_price = levels.get("current_price", 0.0)
                ann.target_price = levels.get("target_price", 0.0)
                ann.limit_price = levels.get("limit_price", 0.0)
                ann.exit_price = levels.get("exit_price", 0.0)
                ann.reliability = levels.get("reliability", "No reliable trading levels available.")
                ann.distance_to_52w_high = levels.get("distance_to_52w_high", 0.0)
                ann.distance_to_52w_low = levels.get("distance_to_52w_low", 0.0)
                ann.trend = levels.get("trend", "")
                high_catalyst_announcements.append(ann)
                
            # 7. Storage
            storage.insert_announcement(ann.id, ann.pdf_hash, ann.title, ann.company, ann.date)
            storage.update_announcement(ann.id, processed=True, catalyst_score=ann.catalyst_score)
            
        except Exception as e:
            logger.error(f"Failed to process {ann_id}: {e}")
            
        finally:
            # Cleanup
            try:
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except OSError as e:
                logger.warning(f"Failed to remove PDF {pdf_path}: {e}")

    # Send Email
    if high_catalyst_announcements:
        high_catalyst_announcements.sort(key=lambda x: x.catalyst_score, reverse=True)
        emailer.send_email(high_catalyst_announcements)
    elif raw_announcements: 
        emailer._send_empty_email()
        
    logger.info("Finished processing announcements.")

if __name__ == "__main__":
    main()

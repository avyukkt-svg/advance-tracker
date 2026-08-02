import os
from nse_client import NSEClient
from pdf_processor import PDFProcessor
from table_extractor import TableExtractor
from text_cleaner import TextCleaner
from document_classifier import DocumentClassifier
from section_detector import SectionDetector
from financial_extractor import FinancialExtractor
from event_detector import EventDetector
from primary_selector import PrimarySelector
from catalyst_scorer import CatalystScorer
from sumy_summarizer import SumySummarizer
from emailer import Emailer
from storage import Storage
from config import Config
from models import Announcement
from price_engine import PriceEngine
from utils import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting NSE Catalyst Scanner (Context-Aware Event Engine - AI Free)...")
    
    nse = NSEClient()
    processor = PDFProcessor()
    tab_extractor = TableExtractor()
    cleaner = TextCleaner()
    doc_classifier = DocumentClassifier()
    section_detector = SectionDetector()
    extractor = FinancialExtractor()
    event_detector = EventDetector()
    primary_selector = PrimarySelector()
    scorer = CatalystScorer()
    summarizer = SumySummarizer()
    emailer = Emailer()
    storage = Storage()
    price_engine = PriceEngine()
    
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
        
        # 2. PyMuPDF Processing
        ann.pdf_hash = processor.get_pdf_hash(pdf_path)
        processor.process_pdf(pdf_path, ann)
        
        # 3. Text Cleaning
        ann.cleaned_text = cleaner.clean_blocks(ann.raw_blocks)
        
        # 4. Document Type Detection (Step 1, 2, 11)
        ann.doc_type, ann.doc_type_confidence, ann.allowed_events = doc_classifier.classify_document(ann.title, ann.cleaned_text)
        logger.info(f"Doc Type: {ann.doc_type} (Conf: {ann.doc_type_confidence}%) - Allowed: {ann.allowed_events}")
        
        # 5. Relevant Section Identification (Phase 2)
        weighted_blocks = section_detector.get_weighted_blocks(ann.cleaned_text.split('\n'))
        section_cleaned_text = "\n".join([b[0] for b in weighted_blocks])
        
        # 6. Extract Text Summary (Sumy)
        ann.sumy_summary = summarizer.summarize(section_cleaned_text, sentences_count=3)
        
        # 7. Financial Data Extraction
        extracted_tables = tab_extractor.extract_tables(pdf_path)
        ann.extracted_financial_data = extractor.extract_financials(extracted_tables, section_cleaned_text)
        
        # 8. Verified Event Detection (Phase 1 & 3)
        # We pass weighted_blocks so the event detector can scale confidence by section priority.
        ann.detected_events, ann.rejected_alternatives = event_detector.detect_events(weighted_blocks, ann.allowed_events)
        
        # 9. Primary Event Selection (Steps 6 & 10)
        ann.primary_event, ann.secondary_events = primary_selector.select_events(
            ann.doc_type, 
            ann.detected_events, 
            ann.doc_type_confidence, 
            ann.extracted_financial_data
        )
        
        # 10. Catalyst Scoring (Step 9)
        ann.market_cap = price_engine.fetch_market_cap(ann.symbol)
        ann.catalyst_score, ann.score_breakdown = scorer.score_announcement(ann.primary_event, ann.extracted_financial_data, ann.doc_type_confidence, ann.market_cap)
        
        logger.info(f"Primary Event: {ann.primary_event.category if ann.primary_event else 'None'}, Catalyst Score: {ann.catalyst_score}")
        
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
            
        # 11. Storage & Observability (Phase 10)
        storage.insert_announcement(ann.id, ann.pdf_hash, ann.title, ann.company, ann.date)
        storage.update_announcement(ann.id, processed=True, catalyst_score=ann.catalyst_score)
        
        import json
        audit_log = {
            "ann_id": ann.id,
            "company": ann.company,
            "doc_type": ann.doc_type,
            "events_considered": len(ann.detected_events),
            "events_rejected": len(ann.rejected_alternatives),
            "reasons": ann.rejected_alternatives,
            "primary_event": ann.primary_event.category if ann.primary_event else "None",
            "catalyst_score": ann.catalyst_score,
            "score_breakdown": [f"{b.reason}: {b.points}" for b in ann.score_breakdown] if ann.score_breakdown else []
        }
        logger.info(f"AUDIT_LOG: {json.dumps(audit_log)}")

        # Cleanup
        try:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
        except OSError as e:
            logger.warning(f"Failed to remove PDF {pdf_path}: {e}")

    # 10. Send Email
    if high_catalyst_announcements:
        high_catalyst_announcements.sort(key=lambda x: x.catalyst_score, reverse=True)
        emailer.send_email(high_catalyst_announcements)
    elif raw_announcements: 
        emailer._send_empty_email()
        
    logger.info("Finished processing announcements.")

if __name__ == "__main__":
    main()

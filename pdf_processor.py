import os
import fitz
import hashlib
import functools
from typing import List, Dict, Any, Tuple, Optional
from utils import get_logger
from models import Announcement

logger = get_logger(__name__)

class PDFProcessor:
    def __init__(self):
        pass

    @functools.lru_cache(maxsize=100)
    def extract_text(self, file_path: str) -> Optional[str]:
        if not file_path or not os.path.exists(file_path):
            return ""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None

    def get_pdf_hash(self, file_path: str) -> str:
        if not file_path or not os.path.exists(file_path):
            return ""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read()
                hasher.update(buf)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing PDF {file_path}: {e}")
            return ""

    def _determine_page_class(self, page_num: int, text: str) -> str:
        text_lower = text.lower()
        if page_num == 0:
            return "Cover Page"
        if "financial results" in text_lower or "statement of profit" in text_lower or "balance sheet" in text_lower:
            return "Financial Results"
        if "notes:" in text_lower or "notes to" in text_lower:
            return "Notes"
        if "annexure" in text_lower:
            return "Annexure"
        return "Body"

    def _extract_headings(self, doc: fitz.Document, ann: Announcement):
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            try:
                # Use dict extraction to get font properties
                page_dict = page.get_text("dict")
                for block in page_dict.get("blocks", []):
                    if block.get("type") == 0: # text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                size = span.get("size", 10)
                                flags = span.get("flags", 0)
                                is_bold = (flags & 2**4) != 0 # Check for bold flag (simplified)
                                text = span.get("text", "").strip()
                                
                                if not text:
                                    continue
                                
                                # Heuristic for heading detection based on size and weight
                                if size > 16 or (size > 14 and is_bold):
                                    ann.headings["Main Heading"].append(text)
                                elif size > 12 and is_bold:
                                    ann.headings["Subheading"].append(text)
                                elif is_bold:
                                    ann.headings["Section Heading"].append(text)
            except Exception as e:
                logger.warning(f"Error extracting dict headings from page {page_num}: {e}")

    def process_pdf(self, file_path: str, ann: Announcement):
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return
            
        try:
            doc = fitz.open(file_path)
            ann.page_count = len(doc)
            
            ann.pdf_metadata = {
                "author": doc.metadata.get("author", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "is_encrypted": doc.is_encrypted,
                "file_size": os.path.getsize(file_path)
            }
            logger.info(f"Metadata extracted: {ann.pdf_metadata}")

            # Extract headings using font sizes
            self._extract_headings(doc, ann)

            blocks_data = []
            
            # Cap processing at 50 pages for performance
            max_pages = min(len(doc), 50)
            
            for page_num in range(max_pages):
                page = doc.load_page(page_num)
                
                # Check for images (OCR flag)
                images = page.get_images(full=True)
                if images and len(page.get_text("text").strip()) < 50:
                    ann.needs_ocr = True
                    logger.info(f"Page {page_num+1} appears to be a scanned image.")

                # Extract blocks
                blocks = page.get_text("blocks")
                page_text = ""
                for b in blocks:
                    if b[6] == 0:  # text block
                        text = b[4].strip()
                        if text:
                            page_text += text + "\n"
                            blocks_data.append({
                                "page_num": page_num + 1,
                                "bbox": (b[0], b[1], b[2], b[3]),
                                "text": text
                            })
                            
                # Classify page
                ann.page_classifications[page_num + 1] = self._determine_page_class(page_num, page_text)

            ann.raw_blocks = blocks_data
            doc.close()
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path} via PyMuPDF: {e}")

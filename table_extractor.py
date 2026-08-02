import fitz
import re
import functools
from typing import List, Dict, Any
from utils import get_logger

logger = get_logger(__name__)

class TableExtractor:
    def __init__(self):
        # Basic understanding of table types
        self.financial_headers = [r"quarter ended", r"year ended", r"yoy", r"qoq", r"revenue", r"ebitda", r"pat", r"income"]
        self.voting_headers = [r"resolution", r"for", r"against", r"invalid", r"votes", r"promoter"]
        
    def _classify_table(self, text_chunk: str) -> str:
        text_lower = text_chunk.lower()
        if re.search(r"quarterly results|financial results", text_lower):
            return "Quarterly Results Table"
        elif re.search(r"revenue|total income", text_lower):
            return "Revenue Table"
        elif re.search(r"profit after tax|pat|net profit", text_lower):
            return "PAT Table"
        elif re.search(r"ebitda|operating profit", text_lower):
            return "EBITDA Table"
        elif re.search(r"margin", text_lower):
            return "Margins Table"
        elif re.search(r"shareholding|promoter|public share", text_lower):
            return "Shareholding Table"
        elif re.search(r"dividend|interim dividend", text_lower):
            return "Dividend Table"
        elif re.search(r"bonus issue|bonus share", text_lower):
            return "Bonus Table"
        elif re.search(r"voting|resolution|for|against|abstain", text_lower):
            return "Voting Table"
        elif re.search(r"contract|order|value|execution", text_lower):
            return "Contract Details Table"
        
        # Fallback to general financial if generic headers exist
        for f in self.financial_headers:
            if re.search(f, text_lower):
                return "Financial Results Table"
        return "General Table"

    @functools.lru_cache(maxsize=100)
    def extract_tables(self, pdf_path: str) -> list[dict]:
        """
        Returns a list of dictionaries with table data and its classification.
        Example: [{"type": "Voting Table", "data": [[...]]}]
        """
        extracted_tables = []
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                tabs = page.find_tables()
                if tabs:
                    for tab in tabs:
                        data = tab.extract()
                        if data:
                            # Flatten table to a string to classify it based on its headers/contents
                            flat_text = " ".join([str(item) for row in data for item in row if item])
                            tab_type = self._classify_table(flat_text)
                            
                            # Clean up None values that PyMuPDF might insert
                            cleaned_data = [[str(cell).strip() if cell else "" for cell in row] for row in data]
                            extracted_tables.append({"type": tab_type, "data": cleaned_data})
            doc.close()
        except Exception as e:
            logger.error(f"Error opening PDF for table extraction {pdf_path}: {e}")
            
        return extracted_tables

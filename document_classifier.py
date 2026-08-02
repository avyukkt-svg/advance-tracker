import re
from typing import Tuple, List
from utils import get_logger
from models import Announcement

logger = get_logger(__name__)

class DocumentClassifier:
    """
    Step 1: Document Type Detection
    Step 2: Document Rule Engine
    Step 11: Negative Context Detection
    """
    
    def __init__(self):
        # Explicit primary document types
        self.doc_types = [
            "AGM Notice", "Board Meeting Notice", "Postal Ballot", "Voting Results",
            "Investor Presentation", "Compliance Filing", "General Disclosure",
            "Quarterly Results", "Annual Results", "Dividend", "Special Dividend",
            "Bonus Issue", "Stock Split", "Buyback", "Rights Issue",
            "Merger", "Scheme of Amalgamation", "Acquisition",
            "Management Change", "Credit Rating", "USFDA Approval",
            "Capacity Expansion", "Litigation", "Regulatory Action",
            "Government Contract", "Order Win"
        ]

        # The mapping of Document Type -> Allowed Events
        # If an event is NOT in the allowed list, it is blocked unless explicit override is detected.
        self.allowed_events_matrix = {
            "AGM Notice": ["AGM", "Voting", "Management Change"],
            "Board Meeting Notice": ["Management Change", "Fund Raise", "Dividend", "Bonus Issue", "Stock Split"],
            "Quarterly Results": ["Quarterly Results", "Dividend", "Bonus Issue", "Management Change"],
            "Government Contract": ["Government Contract", "Order Win"],
            "Order Win": ["Order Win", "Government Contract"],
            "Merger": ["Merger", "Scheme of Amalgamation"],
            "Acquisition": ["Acquisition"],
            "Buyback": ["Buyback"],
            "Stock Split": ["Stock Split"],
            "Bonus Issue": ["Bonus Issue"],
            "Dividend": ["Dividend", "Special Dividend"],
            "USFDA Approval": ["USFDA Approval"],
            "Credit Rating": ["Credit Rating"]
        }
        
        # Negative context words that crush the confidence of events
        self.negative_words = [
            r"\bnotice\b", r"\bagenda\b", r"\bproposal\b", r"\bdraft\b",
            r"\bwill consider\b", r"\bexpected\b", r"\bproposed\b",
            r"\btribunal order\b", r"\bcourt order\b", r"\bproxy\b",
            r"\bmeeting\b", r"\bvoting\b", r"\bpostal ballot\b"
        ]

    def classify_document(self, title: str, text: str) -> Tuple[str, int, List[str]]:
        """
        Returns (Document Type, Confidence, Allowed Events)
        Uses both the title and the first 2000 characters of the PDF body.
        """
        title_lower = title.lower()
        text_lower = text[:2000].lower() # Extended Preamble
        
        # 1. Identify Document Type
        doc_type = "General Disclosure"
        confidence = 0
        
        # Title matches heavily influence the prediction
        if "agm" in title_lower or "annual general meeting" in title_lower:
            doc_type = "AGM Notice"
            confidence = 100
        elif "board meeting" in title_lower or "notice of board" in title_lower:
            # But the body might reveal the actual outcome
            if "outcome" in title_lower or "approved" in text_lower or "recommended" in text_lower:
                if "dividend" in text_lower:
                    doc_type = "Dividend"
                    confidence = 85
                elif "financial results" in text_lower or "quarterly results" in text_lower:
                    doc_type = "Quarterly Results"
                    confidence = 85
                elif "buyback" in text_lower:
                    doc_type = "Buyback"
                    confidence = 85
                elif "split" in text_lower or "sub-division" in text_lower:
                    doc_type = "Stock Split"
                    confidence = 85
                else:
                    doc_type = "Board Meeting Notice"
                    confidence = 90
            else:
                doc_type = "Board Meeting Notice"
                confidence = 100
        elif "postal ballot" in title_lower:
            doc_type = "Postal Ballot"
            confidence = 100
        elif "voting results" in title_lower:
            doc_type = "Voting Results"
            confidence = 100
        elif "presentation" in title_lower and ("investor" in title_lower or "analyst" in title_lower):
            doc_type = "Investor Presentation"
            confidence = 100
        elif "financial results" in title_lower or "quarterly results" in title_lower:
            doc_type = "Quarterly Results"
            confidence = 100
        elif "order" in title_lower or "contract" in title_lower or "award" in title_lower:
            if "government" in text_lower or "railway" in text_lower or "nhai" in text_lower or "psu" in text_lower:
                doc_type = "Government Contract"
            else:
                doc_type = "Order Win"
            confidence = 90
        elif "acquisition" in title_lower:
            doc_type = "Acquisition"
            confidence = 90
        elif "merger" in title_lower or "amalgamation" in title_lower:
            doc_type = "Merger"
            confidence = 90
        elif "credit rating" in title_lower:
            doc_type = "Credit Rating"
            confidence = 90
        elif "usfda" in title_lower or "fda" in title_lower:
            doc_type = "USFDA Approval"
            confidence = 90
        elif "buyback" in title_lower:
            doc_type = "Buyback"
            confidence = 90
        elif "stock split" in title_lower or "sub-division" in title_lower:
            doc_type = "Stock Split"
            confidence = 90
        elif "bonus issue" in title_lower:
            doc_type = "Bonus Issue"
            confidence = 90
        elif "dividend" in title_lower:
            doc_type = "Dividend"
            confidence = 90
        else:
            # Fallback to body scan if title is very generic
            if "dividend" in text_lower and "recommended" in text_lower:
                doc_type = "Dividend"
                confidence = 70
            elif "order" in text_lower and "awarded" in text_lower:
                doc_type = "Order Win"
                confidence = 70
            
        # 2. Get Allowed Events
        allowed_events = self.allowed_events_matrix.get(doc_type, ["ALL"])
        
        # 3. Calculate Negative Context Penalty
        penalty = 0
        if doc_type not in ["AGM Notice", "Board Meeting Notice"]:
            for word in self.negative_words:
                if re.search(word, title_lower):
                    penalty += 30
                if re.search(word, text_lower):
                    # Only minor penalty here, smart negative context is handled in event_detector
                    penalty += 5
                    
        confidence = max(0, confidence - penalty)
        
        # Improvement 4 & 12: Unknown Document
        if confidence < 50:
            doc_type = "Unknown Document"
            allowed_events = ["ALL"]
        
        return doc_type, confidence, allowed_events

from typing import List, Dict, Any, Tuple
from utils import get_logger
import re

logger = get_logger(__name__)

class SectionDetector:
    """
    Phase 2: Section Priority
    Identifies bounds of non-catalyst sections like Voting Tables, Signatures, Annexures,
    and assigns confidence weights.
    """
    
    def __init__(self):
        self.section_weights = {
            "Resolution": 1.0,
            "Order Details": 1.0,
            "Financial Results": 0.95,
            "Notice": 0.40,
            "Agenda": 0.20,
            "Voting": 0.0,
            "Annexure": 0.0,
            "Signature": 0.0,
            "General": 0.50
        }
        
    def get_weighted_blocks(self, blocks: List[str]) -> List[Tuple[str, str, float]]:
        """
        Returns a list of tuples containing (block_text, section_name, weight).
        """
        weighted_blocks = []
        current_section = "General"
        
        for block in blocks:
            block_lower = block.lower()
            
            # Detect section shifts
            if re.search(r"\b(resolution|resolves?)\b", block_lower):
                current_section = "Resolution"
            elif re.search(r"\b(order details|contract details)\b", block_lower):
                current_section = "Order Details"
            elif re.search(r"\b(financial results|statement of profit)\b", block_lower):
                current_section = "Financial Results"
            elif re.search(r"\b(notice)\b", block_lower):
                current_section = "Notice"
            elif re.search(r"\b(agenda)\b", block_lower):
                current_section = "Agenda"
            elif re.search(r"\b(voting results|proxy form)\b", block_lower):
                current_section = "Voting"
            elif re.search(r"\b(annexure|notes to financial)\b", block_lower):
                current_section = "Annexure"
            elif re.search(r"\b(signatures|for and on behalf)\b", block_lower):
                current_section = "Signature"
                
            weight = self.section_weights.get(current_section, 0.50)
            
            # If weight > 0, we can keep it. But we'll just return everything and let event_detector handle it.
            if weight > 0:
                weighted_blocks.append((block, current_section, weight))
                
        return weighted_blocks

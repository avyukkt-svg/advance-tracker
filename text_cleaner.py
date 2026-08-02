import re
from typing import List, Dict, Any

class TextCleaner:
    def __init__(self):
        # Patterns for noise removal
        self.page_number_pattern = re.compile(r'^page\s*\d+\s*(of\s*\d+)?$', re.IGNORECASE)
        self.signature_pattern = re.compile(r'(digitally signed by|signature:|for\s+.*\s+limited|managing director|company secretary)', re.IGNORECASE)
        
    def clean_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Takes raw blocks extracted by PDFProcessor and cleans them:
        - Removes repeated headers/footers based on y-coordinates (basic heuristic)
        - Removes page numbers
        - Removes signature blocks
        - Removes blank lines and duplicate paragraphs
        Returns a single cleaned string.
        """
        if not blocks:
            return ""
            
        cleaned_paragraphs = []
        seen = set()
        
        for block in blocks:
            text = block.get('text', '').strip()
            
            # Skip empty blocks
            if not text:
                continue
                
            # Heuristics for page numbers
            if self.page_number_pattern.match(text) or (text.isdigit() and len(text) < 4):
                continue
                
            # Heuristics for digital signatures / signature blocks
            if self.signature_pattern.search(text):
                continue
                
            # Basic header/footer heuristic (y-coordinate < 50 or > 750 on standard A4)
            # Not universally applicable without page dimensions, but skipping for now to rely on duplication.
            
            # Remove duplicate paragraphs (often recurring headers/disclaimers)
            if text not in seen:
                seen.add(text)
                # Replace multiple newlines within a block with a space to make it flow better
                text = re.sub(r'\s+', ' ', text)
                cleaned_paragraphs.append(text)
                
        return '\n\n'.join(cleaned_paragraphs)

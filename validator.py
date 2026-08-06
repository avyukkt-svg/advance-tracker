import re
from models import AIAnalysis
from utils import get_logger

logger = get_logger(__name__)

class Validator:
    @staticmethod
    def validate_analysis(analysis: AIAnalysis, raw_text: str) -> AIAnalysis:
        """
        Validates that numbers/dates/percentages in the extracted financial data
        actually exist in the raw_text. If not, discards the field.
        """
        # Normalize text for easier searching (e.g. remove commas in numbers in raw text)
        raw_text_normalized = raw_text.replace(',', '')
        
        financials = analysis.key_financial_numbers.model_dump()
        
        for field_name, field_value in financials.items():
            if not field_value:
                continue
                
            # Extract all numbers from the AI's answer for this field
            # This matches digits, optionally with decimals
            numbers_in_value = re.findall(r'\b\d+(?:\.\d+)?\b', str(field_value).replace(',', ''))
            
            for num in numbers_in_value:
                # Check if this exact number string exists in the raw text
                if num not in raw_text_normalized:
                    logger.warning(f"Validation failed for '{field_name}'. Hallucinated value: {num}. Discarding field.")
                    setattr(analysis.key_financial_numbers, field_name, None)
                    break  # Discard the whole field and move to the next
                    
        return analysis

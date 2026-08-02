import re
from datetime import datetime
from typing import Dict, Any, List
from utils import get_logger

logger = get_logger(__name__)

class FinancialExtractor:
    """
    Step 7: Financial Extraction
    Step 8: Date Extraction
    """
    
    def __init__(self):
        # Specific regex rules per category
        self.money_pattern = r"(?:rs\.?|inr|₹|usd|\$)\s*([\d,]+(?:\.\d+)?)\s*(crores?|crs?|millions?|mn|lakhs?|lacs?)?"
        
    def _is_valid_date(self, date_str: str) -> bool:
        try:
            # Example strings: "12-10-2023", "38/13/11" (which will fail)
            # Remove any trailing periods
            date_str = date_str.strip('.,')
            if '-' in date_str:
                datetime.strptime(date_str, "%d-%m-%Y")
                return True
            elif '/' in date_str:
                datetime.strptime(date_str, "%d/%m/%Y")
                return True
        except ValueError:
            return False
        return True
        
    def extract_financials(self, tables: list[dict], text: str) -> dict:
        """
        Extracts financial metrics and identifies order values/dividend amounts.
        Now supports basic QoQ / YoY growth extraction from Financial Results Tables.
        """
        financials = {
            "order_values": [],
            "dividend_amounts": [],
            "revenue": None,
            "profit": None,
            "yoy_growth": None,
            "qoq_growth": None
        }
        
        # 1. Parse text for explicit Order Values or Dividends using Regex
        # Find explicit order values like "Rs 500 Crore" or "₹ 1,500 million"
        order_pattern = r"(?:rs\.?|₹|inr)\s*([\d,]+(?:\.\d+)?)\s*(crore|cr|million|mn|lakh|billion)"
        for match in re.finditer(order_pattern, text.lower()):
            val = f"₹{match.group(1)} {match.group(2)}"
            if val not in financials["order_values"]:
                financials["order_values"].append(val)
                
        # Find explicit dividend amounts
        div_pattern = r"(?:dividend\s+of\s+)(?:rs\.?|₹|inr)\s*([\d,]+(?:\.\d+)?)(?:\s*per\s+share)"
        for match in re.finditer(div_pattern, text.lower()):
            val = f"₹{match.group(1)} per share"
            if val not in financials["dividend_amounts"]:
                financials["dividend_amounts"].append(val)
                
        # 2. Extract Growth from Financial Tables
        for table_dict in tables:
            if table_dict["type"] == "Financial Results Table":
                data = table_dict["data"]
                # Scan table rows for Revenue/Income and Profit/PAT
                for row in data:
                    row_text = " ".join([str(c).lower() for c in row if c])
                    
                    if "revenue" in row_text or "total income" in row_text:
                        # Extract the first two numbers as Current and Previous period
                        nums = [float(re.sub(r'[^\d.]', '', str(c))) for c in row if c and re.search(r'\d', str(c))]
                        if len(nums) >= 2 and nums[1] != 0:
                            growth = ((nums[0] - nums[1]) / nums[1]) * 100
                            financials["revenue"] = nums[0]
                            financials["yoy_growth"] = f"{growth:+.2f}%"
                            
                    elif "profit after tax" in row_text or "pat" in row_text or "net profit" in row_text:
                        nums = [float(re.sub(r'[^\d.]', '', str(c))) for c in row if c and re.search(r'\d', str(c))]
                        if len(nums) >= 2 and nums[1] != 0:
                            financials["profit"] = nums[0]
        
        return financials
        
    def extract(self, cleaned_text: str) -> Dict[str, Any]:
        data = {
            "order_values": [],
            "revenue": [],
            "profit": [],
            "historical_revenue": [],
            "dividend_amounts": [],
            "bonus_ratios": [],
            "split_ratios": [],
            "gov_agencies": [],
            "valid_dates": []
        }
        
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text.replace("\n", " "))
        
        for sentence in sentences:
            sent_lower = sentence.lower()
            
            # Dates (Step 8)
            dates = re.findall(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", sentence)
            for d in dates:
                if self._is_valid_date(d):
                    data["valid_dates"].append(d)
                    
            # Bonus / Split Ratio
            if "bonus" in sent_lower or "split" in sent_lower or "sub-division" in sent_lower:
                ratios = re.findall(r"\b(\d+\s*:\s*\d+)\b", sentence)
                if "bonus" in sent_lower:
                    data["bonus_ratios"].extend(ratios)
                else:
                    data["split_ratios"].extend(ratios)
                    
            # Financial Data
            monies = re.findall(self.money_pattern, sentence, re.IGNORECASE)
            for val, unit in monies:
                amt_str = f"₹{val} {unit}".strip() if unit else f"₹{val}"
                
                if "dividend" in sent_lower:
                    data["dividend_amounts"].append(amt_str)
                elif "order" in sent_lower or "contract" in sent_lower or "award" in sent_lower:
                    data["order_values"].append(amt_str)
                elif "revenue" in sent_lower or "sales" in sent_lower:
                    if "ended" in sent_lower and "2022" in sent_lower: # basic historical check
                        data["historical_revenue"].append(amt_str)
                    else:
                        data["revenue"].append(amt_str)
                elif "profit" in sent_lower or "pat" in sent_lower or "ebitda" in sent_lower:
                    data["profit"].append(amt_str)
                    
            # Government Agencies
            if "order" in sent_lower or "contract" in sent_lower:
                agencies = re.findall(r"(Indian Railways|NHAI|Ministry of \w+|[\w\s]+ Municipal Corporation)", sentence, re.IGNORECASE)
                data["gov_agencies"].extend(agencies)
                
        # Deduplicate
        for key in data:
            data[key] = list(set(data[key]))
            
        return data

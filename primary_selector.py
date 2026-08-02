from typing import List, Tuple
from models import DetectedEvent
from utils import get_logger

logger = get_logger(__name__)

class PrimarySelector:
    """
    Step 6: Primary Event
    Step 10, 11: Contradiction Detection
    Step 12: Uncertainty Handling ("Needs Manual Review")
    """
    
    def __init__(self):
        # Priority mapping to resolve conflicts
        self.priority = {
            "Merger": 100,
            "USFDA Approval": 95,
            "Government Contract": 90,
            "Order Win": 85,
            "Acquisition": 80,
            "Bonus Issue": 75,
            "Stock Split": 70,
            "Buyback": 65,
            "Dividend": 60,
            "Quarterly Results": 50,
            "AGM Notice": 10
        }

    def select_events(self, doc_type: str, events: List[DetectedEvent], doc_type_confidence: int = 100, financial_data: dict = None) -> Tuple[DetectedEvent, List[DetectedEvent]]:
        if not events:
            return None, []
            
        def _calculate_event_score(event: DetectedEvent) -> float:
            score = 0.0
            
            # 1. Evidence Strength (35%)
            score += (event.confidence / 100.0) * 35.0
            
            # 2. Document Confidence (25%)
            score += (doc_type_confidence / 100.0) * 25.0
            
            # 3. Document Compatibility (20%)
            compat = 20.0
            if doc_type in ["AGM Notice", "Board Meeting Notice", "Investor Presentation"] and event.category in ["Government Contract", "Order Win", "USFDA Approval"]:
                compat = 0.0 # High contradiction
            elif doc_type == "Unknown Document":
                compat = 10.0 # Neutral
            score += compat
            
            # 4. Financial Magnitude (10%)
            mag = 0.0
            if financial_data:
                if financial_data.get("order_values") or financial_data.get("revenue") or financial_data.get("dividend_amounts"):
                    mag = 10.0
            score += mag
            
            # 5. Event Priority (10%)
            priority_val = self.priority.get(event.category, 0)
            score += (priority_val / 100.0) * 10.0
            
            return score
            
        sorted_events = sorted(events, key=_calculate_event_score, reverse=True)
        
        primary_event = sorted_events[0]
        secondary_events = sorted_events[1:]
        
        # Improvement 11 & 12: Uncertainty and Contradiction Handling
        # If the overall score is too low, fall back.
        if _calculate_event_score(primary_event) < 60:
            primary_event.category = "Needs Manual Review"
            primary_event.evidence = "Overall primary score too low across all 5 metrics."
            
        return primary_event, secondary_events

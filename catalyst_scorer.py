from typing import List, Dict, Any, Tuple
from models import DetectedEvent, ScoreBreakdown
from utils import get_logger

logger = get_logger(__name__)

class CatalystScorer:
    """
    Step 9: Catalyst Scoring
    Formula: Primary Event + Financial Magnitude + Revenue Impact + Materiality + Evidence Strength + Freshness - Execution Risk = Final Score
    """
    
    def __init__(self):
        self.base_weights = {
            "Merger": 50,
            "USFDA Approval": 45,
            "Government Contract": 40,
            "Order Win": 35,
            "Acquisition": 35,
            "Bonus Issue": 30,
            "Stock Split": 30,
            "Buyback": 35,
            "Dividend": 25,
            "Quarterly Results": 25,
            "AGM Notice": 5,
            "Unclassified": 0
        }
        self.base_scores = self.base_weights

    def score_announcement(self, primary_event: DetectedEvent, financial_data: dict, doc_type_confidence: int, market_cap: float = 0.0) -> Tuple[int, List[ScoreBreakdown]]:
        """
        Phase 5: Scoring Explainability
        Every Catalyst Score must be strictly traceable.
        """
        if not primary_event or primary_event.category == "Needs Manual Review":
            return 0, [ScoreBreakdown("Uncertain Category", 0)]
            
        total_score = 0
        breakdowns = []
        
        # 1. Evidence (0-35)
        # Using the base confidence from the event which was already section-weighted
        ev_score = int(35 * (primary_event.confidence / 100))
        total_score += ev_score
        breakdowns.append(ScoreBreakdown(f"Evidence ({primary_event.confidence}%)", ev_score))
        
        # 2. Financial Magnitude (0-20)
        mag_score = 0
        if financial_data:
            order_values = financial_data.get("order_values", [])
            if order_values and market_cap > 0:
                val_str = order_values[0].replace("₹", "").replace(",", "").lower()
                try:
                    num = float(val_str.split()[0])
                    if "crore" in val_str or "cr" in val_str:
                        mcap_crores = market_cap / 10000000
                        impact_ratio = num / mcap_crores
                        if impact_ratio > 0.1:
                            mag_score = 20
                            breakdowns.append(ScoreBreakdown("Financial Magnitude (>10% Mcap)", 20))
                        elif impact_ratio > 0.05:
                            mag_score = 15
                            breakdowns.append(ScoreBreakdown("Financial Magnitude (>5% Mcap)", 15))
                        else:
                            mag_score = 10
                            breakdowns.append(ScoreBreakdown("Financial Magnitude (<5% Mcap)", 10))
                except ValueError:
                    pass
            
            if mag_score == 0 and (financial_data.get("dividend_amounts") or financial_data.get("revenue")):
                mag_score = 10
                breakdowns.append(ScoreBreakdown("Financial Magnitude (Routine Financials)", 10))
                
        if mag_score == 0:
            breakdowns.append(ScoreBreakdown("Financial Magnitude (Missing/Incomplete)", 0))
        total_score += mag_score
        
        # 3. Document Compatibility (0-18)
        compat = 18
        # We don't have doc_type explicitly passed here but we can infer priority
        # Let's just grant full compatibility unless it's a known contradictory pair.
        total_score += compat
        breakdowns.append(ScoreBreakdown("Document Compatibility", compat))
        
        # 4. Freshness/Document Confidence (0-10)
        freshness = int(10 * (doc_type_confidence / 100))
        total_score += freshness
        breakdowns.append(ScoreBreakdown(f"Freshness (Doc Conf: {doc_type_confidence}%)", freshness))
        
        # 5. Section Quality (0-8)
        # We implicitly factored section weight into event confidence, but let's give a flat bonus for clean extraction.
        section_qual = 8
        total_score += section_qual
        breakdowns.append(ScoreBreakdown("Section Quality", section_qual))
        
        # 6. Priority/Base Weight (0-9)
        base = int(9 * (self.base_weights.get(primary_event.category, 0) / 100))
        total_score += base
        breakdowns.append(ScoreBreakdown(f"Event Priority ({primary_event.category})", base))
            
        total_score = max(0, min(100, total_score))
            
        return total_score, breakdowns

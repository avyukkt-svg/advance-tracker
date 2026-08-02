import re
import nltk
from typing import List, Tuple
from models import DetectedEvent
from utils import get_logger

# Ensure tokenizer is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt_tab')

logger = get_logger(__name__)

class EventDetector:
    """
    Step 4: Verified Event Detection
    Step 5: Event Evidence
    Improvements: Relationship-Based Detection & Smart Negative Context
    """
    
    def __init__(self):
        # Strict logic: Category -> { "actions": [], "nouns": [], "conditions": [] }
        self.rules = {
            "Government Contract": {
                "actions": [r"\breceived\b", r"\bawarded\b", r"\bsecured\b", r"\bwon\b", r"\bbagged\b"],
                "nouns": [r"\bcontract\b", r"\bletter of award\b", r"\bletter of acceptance\b", r"\bpurchase order\b", r"\bwork order\b"],
                "conditions": [r"(?:government|railways?|nhai|psu|ministry|corporation)"]
            },
            "Order Win": {
                "actions": [r"\breceived\b", r"\bawarded\b", r"\bsecured\b", r"\bwon\b", r"\bbagged\b"],
                "nouns": [r"\bcontract\b", r"\bletter of award\b", r"\border\b"],
                "conditions": [r"(?:crores?|millions?|usd)"]
            },
            "Dividend": {
                "actions": [r"\bdeclared\b", r"\brecommended\b", r"\bapproved\b"],
                "nouns": [r"\bdividend\b", r"\binterim dividend\b", r"\bfinal dividend\b"],
                "conditions": []
            },
            "Bonus Issue": {
                "actions": [r"\bapproved\b", r"\brecommended\b"],
                "nouns": [r"\bbonus\b", r"\bcapitalisation\b"],
                "conditions": [r"\d+\s*:\s*\d+"] 
            },
            "Stock Split": {
                "actions": [r"\bapproved\b", r"\brecommended\b"],
                "nouns": [r"\bsplit\b", r"\bsub-division\b"],
                "conditions": [r"\d+\s*:\s*\d+", r"face value"]
            },
            "Merger": {
                "actions": [r"\bapproved\b", r"\bsanctioned\b"],
                "nouns": [r"\bmerger\b", r"\bamalgamation\b", r"\bscheme of arrangement\b"],
                "conditions": [r"nclt", r"tribunal"]
            },
            "Acquisition": {
                "actions": [r"\bapproved\b", r"\bacquired\b", r"\bexecuted\b"],
                "nouns": [r"\bacquisition\b", r"\bshare purchase agreement\b", r"\bstake\b"],
                "conditions": [r"crore", r"million", r"percentage", r"%"]
            },
            "USFDA Approval": {
                "actions": [r"\breceived\b", r"\bgranted\b", r"\bapproved\b"],
                "nouns": [r"\banda\b", r"\busfda\b", r"\bfda\b", r"\btentative approval\b", r"\bfinal approval\b"],
                "conditions": []
            }
        }
        
        self.negative_modifiers = [r"\bproposal\b", r"\bexpected\b", r"\bdraft\b", r"\bwill consider\b", r"\bproposed\b"]
        
    def _smart_negative_context_check(self, sentence: str) -> int:
        """
        Returns a confidence penalty.
        If "approved" and "proposal" are in the same sentence, the negative context of "proposal" is neutralized.
        """
        sent_lower = sentence.lower()
        penalty = 0
        
        has_negative = any(re.search(mod, sent_lower) for mod in self.negative_modifiers)
        
        if has_negative:
            # If they approved the proposal, it's a real event, no penalty
            if re.search(r"\bapproved\b", sent_lower) or re.search(r"\bsanctioned\b", sent_lower):
                penalty = 0
            else:
                penalty = 60 # Severe penalty for speculative language
                
        return penalty

    def detect_events(self, weighted_blocks: List[Tuple[str, str, float]], allowed_events: List[str]) -> Tuple[List[DetectedEvent], List[str]]:
        """
        Phase 1 & 3: Event Relationship Graph & Evidence Validation.
        Phase 2: Section Priority weighting.
        """
        detected = []
        rejected_alternatives = []
        
        for category, rule in self.rules.items():
            if allowed_events != ["ALL"] and category not in allowed_events:
                rejected_alternatives.append(f"{category}: Blocked by document classifier (not in allowed_events).")
                continue
                
            category_found = False
            for block_idx, (block_text, section_name, section_weight) in enumerate(weighted_blocks):
                if category_found: break
                
                # If section weight is 0 (like Voting or Annexure), ignore it for event detection
                if section_weight == 0:
                    continue
                    
                sentences = nltk.tokenize.sent_tokenize(block_text.replace("\n", " "))
                
                for i, sentence in enumerate(sentences):
                    sent_lower = sentence.lower()
                    
                    # Check Action
                    action_found = False
                    for act in rule["actions"]:
                        if re.search(act, sent_lower):
                            action_found = True
                            break
                            
                    # Check Noun
                    noun_found = False
                    for noun in rule["nouns"]:
                        if re.search(noun, sent_lower):
                            noun_found = True
                            break
                            
                    if action_found and not noun_found:
                        rejected_alternatives.append(f"{category}: Action found in sentence but missing required Noun checklist.")
                    elif not action_found and noun_found:
                        rejected_alternatives.append(f"{category}: Noun found in sentence but missing required Action checklist.")
                            
                    # Check Condition (Customer/Entity)
                    condition_met = True
                    if rule["conditions"]:
                        condition_met = False
                        # Phase 1: Maximum Relationship Distance is neighboring sentences
                        context_sentences = sent_lower
                        if i > 0:
                            context_sentences += " " + sentences[i-1].lower()
                        if i < len(sentences) - 1:
                            context_sentences += " " + sentences[i+1].lower()
                            
                        for cond in rule["conditions"]:
                            if re.search(cond, context_sentences):
                                condition_met = True
                                break
                                
                    if action_found and noun_found and not condition_met:
                        rejected_alternatives.append(f"{category}: Action and Noun found, but failed Relationship Graph condition check in neighboring sentences.")
                                
                    # Phase 1 & 3 Validation Checklist
                    if action_found and noun_found and condition_met:
                        # Base Confidence
                        base_confidence = 95
                        
                        # Smart Negative Context
                        penalty = self._smart_negative_context_check(sent_lower)
                        if penalty > 0:
                            rejected_alternatives.append(f"{category}: Penalized -{penalty} points due to speculative negative context language.")
                        
                        # Apply Section Priority Weight (Phase 2)
                        confidence = max(0, (base_confidence - penalty) * section_weight)
                        
                        # Phase 4 Calibration: Cap at 95 unless it's a perfect match (can be expanded later for fields like Value)
                        confidence = min(95, confidence)
                        
                        detected.append(DetectedEvent(
                            category=category,
                            confidence=confidence,
                            evidence=sentence.strip()
                        ))
                        category_found = True
                        break # Only capture the best evidence sentence per category per block
                        
        return detected, rejected_alternatives

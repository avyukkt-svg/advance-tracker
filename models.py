from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class DetectedEvent:
    category: str
    confidence: int  # 0 to 100
    evidence: str
    rejected_alternatives: List[str] = field(default_factory=list)

@dataclass
class ScoreBreakdown:
    reason: str
    points: int

@dataclass
class Announcement:
    id: str
    company: str
    symbol: str
    title: str
    date: str
    pdf_url: str
    
    # Hashes for deterministic deduplication
    pdf_hash: str = ""
    text_hash: str = ""
    
    # Metadata extracted by PyMuPDF
    pdf_metadata: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 0
    needs_ocr: bool = False
    
    # Extracted structural elements
    raw_blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_classifications: Dict[int, str] = field(default_factory=dict)
    headings: Dict[str, List[str]] = field(default_factory=lambda: {
        "Main Heading": [],
        "Subheading": [],
        "Section Heading": []
    })
    
    tables: List[List[List[str]]] = field(default_factory=list)
    keyword_locations: Dict[str, List[int]] = field(default_factory=dict)
    
    cleaned_text: str = ""
    extracted_financial_data: Dict[str, Any] = field(default_factory=dict)
    
    # Redesigned Intelligence Pipeline Fields
    doc_type: str = "Unclassified"
    doc_type_confidence: int = 0
    allowed_events: List[str] = field(default_factory=list)
    
    primary_event: DetectedEvent = None
    secondary_events: List[DetectedEvent] = field(default_factory=list)
    
    detected_events: List[DetectedEvent] = field(default_factory=list) # kept for backward compatibility during refactor
    rejected_alternatives: List[str] = field(default_factory=list)
    score_breakdown: List[ScoreBreakdown] = field(default_factory=list)
    catalyst_score: int = 0
    processing_status: str = "pending"
    
    # Sumy Summary
    sumy_summary: str = ""
    
    # Pricing Data
    current_price: float = 0.0
    target_price: float = 0.0
    exit_price: float = 0.0
    limit_price: float = 0.0
    reliability: str = ""
    market_cap: float = 0.0
    distance_to_52w_high: float = 0.0
    distance_to_52w_low: float = 0.0
    trend: str = ""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

@dataclass
class DetectedEvent:
    category: str
    confidence: float
    evidence: str

class ScoreBreakdown(BaseModel):
    reason: str
    points: int

class KeyFinancialNumbers(BaseModel):
    revenue: Optional[str] = None
    pat: Optional[str] = None
    ebitda: Optional[str] = None
    margins: Optional[str] = None
    contract_value: Optional[str] = None
    dividend: Optional[str] = None
    buyback: Optional[str] = None
    bonus_ratio: Optional[str] = None
    split_ratio: Optional[str] = None
    fund_raising: Optional[str] = None
    acquisition_value: Optional[str] = None
    market_impact: Optional[str] = None

class RiskItem(BaseModel):
    risk_type: str
    explanation: str

class AIAnalysis(BaseModel):
    document_type: str = Field(description="The type of document, e.g., Quarterly Results, Government Contract, Dividend, etc.")
    primary_event: str = Field(description="Only ONE primary event")
    secondary_events: List[str] = Field(default_factory=list, description="Secondary events only if clearly supported")
    market_importance: str = Field(description="Very High, High, Medium, Low, or Very Low")
    catalyst_score: int = Field(ge=0, le=100, description="Return 0-100 considering impact")
    catalyst_score_breakdown: List[ScoreBreakdown] = Field(description="Complete breakdown of the Catalyst Score")
    key_financial_numbers: KeyFinancialNumbers = Field(description="Key Financial Numbers")
    risk_analysis: List[RiskItem] = Field(default_factory=list, description="Only if supported. Execution Risk, Regulatory Risk, Financial Risk, etc.")
    opportunities: List[str] = Field(default_factory=list, description="Explain positive outcomes")
    investment_impact: str = Field(description="Very Bullish, Bullish, Neutral, Bearish, or Very Bearish")
    investment_impact_explanation: str = Field(description="Explain why")
    one_sentence_summary: str = Field(description="Maximum 25 words")
    executive_summary: str = Field(description="Maximum 250 words. Written for retail investors. Simple English.")

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
    
    # AI Analysis Output
    ai_analysis: Optional[AIAnalysis] = None
    
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
    
    @property
    def catalyst_score(self) -> int:
        return self.ai_analysis.catalyst_score if self.ai_analysis else 0

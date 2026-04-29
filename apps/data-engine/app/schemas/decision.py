from typing import Optional, List
from pydantic import BaseModel


class DecisionResponse(BaseModel):
    sku_id: int
    score: int
    suggestion: str  # BUY, WAIT, AVOID
    confidence: float
    reason: str
    price_score: int
    history_score: int
    coupon_score: int
    risk_score: int
    best_platform: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_delta_percent: Optional[float] = None
    risk_text: Optional[str] = None
    action_label: Optional[str] = None
    action_type: Optional[str] = None
    
    # R1-01 & R1-04 Discount Breakdown
    original_price: Optional[float] = None
    final_price: Optional[float] = None
    total_discount: Optional[float] = None
    discount_details: Optional[List[str]] = None

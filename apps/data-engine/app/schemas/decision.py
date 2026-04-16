from typing import Optional
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

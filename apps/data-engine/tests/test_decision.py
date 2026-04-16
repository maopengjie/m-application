import pytest
from unittest.mock import MagicMock
from app.services.decision_service import DecisionService
from app.schemas.decision import DecisionResponse

class MockSKU:
    def __init__(self, id, price, original_price=None, platform="JD", shop_name="Store"):
        self.id = id
        self.price = price
        self.original_price = original_price
        self.platform = platform
        self.shop_name = shop_name
        self.coupons = []
        self.risk_score = MagicMock(score=95)
        self.product = MagicMock()
        self.product.skus = [self]

def test_get_decision_buy_scenario():
    service = DecisionService()
    
    # Mock repo
    service.product_repo = MagicMock()
    
    # Setup a "BUY" scenario: price is low, history is at min
    mock_sku = MockSKU(id=1, price=7000, original_price=10000)
    service.product_repo.get_sku_by_id.return_value = mock_sku
    
    # Mock history stats: current price (7000) is the min
    service.product_repo.get_price_history_with_stats.return_value = {
        "min_price": 7000,
        "max_price": 9000,
        "avg_price": 8000,
        "current_price": 7000,
        "history": []
    }
    
    # Mock promo service (if needed, but it uses the real one currently)
    # DecisionService uses PromotionService which handles MockSKU if it has price/coupons
    
    db = MagicMock()
    decision = service.get_decision(db, 1)
    
    assert isinstance(decision, DecisionResponse)
    assert decision.score > 75
    assert decision.suggestion == "BUY"
    assert "历史极低价" in decision.reason

def test_get_decision_avoid_scenario():
    service = DecisionService()
    service.product_repo = MagicMock()
    
    # Setup an "AVOID" scenario: price is high, history is at max
    mock_sku = MockSKU(id=2, price=9500, original_price=10000)
    mock_sku.risk_score = MagicMock(score=30) # High risk
    service.product_repo.get_sku_by_id.return_value = mock_sku
    
    service.product_repo.get_price_history_with_stats.return_value = {
        "min_price": 7000,
        "max_price": 9500,
        "avg_price": 8000,
        "current_price": 9500,
        "history": []
    }
    
    db = MagicMock()
    decision = service.get_decision(db, 2)
    
    assert decision.score < 50
    assert decision.suggestion == "AVOID"
    assert "商家存在一定风险" in decision.reason

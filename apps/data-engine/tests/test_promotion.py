import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.services.promotion_service import PromotionService

class MockCoupon:
    def __init__(self, amount, condition_amount=None, start_time=None, end_time=None):
        self.amount = Decimal(str(amount))
        self.condition_amount = Decimal(str(condition_amount)) if condition_amount else None
        self.start_time = start_time
        self.end_time = end_time

class MockSKU:
    def __init__(self, price, coupons=None):
        self.price = Decimal(str(price))
        self.coupons = coupons or []

def test_calculate_final_price_no_coupons():
    sku = MockSKU(price=100.0)
    result = PromotionService.calculate_final_price(sku)
    assert result["final_price"] == 100.0
    assert result["total_discount"] == 0.0
    assert len(result["promotions"]) == 0

def test_calculate_final_price_with_valid_coupon():
    coupon = MockCoupon(amount=10.0, condition_amount=50.0)
    sku = MockSKU(price=100.0, coupons=[coupon])
    result = PromotionService.calculate_final_price(sku)
    assert result["final_price"] == 90.0
    assert result["total_discount"] == 10.0
    assert result["promotions"][0]["amount"] == 10.0

def test_calculate_final_price_with_invalid_coupon():
    coupon = MockCoupon(amount=10.0, condition_amount=200.0)
    sku = MockSKU(price=100.0, coupons=[coupon])
    result = PromotionService.calculate_final_price(sku)
    assert result["final_price"] == 100.0
    assert result["total_discount"] == 0.0

def test_calculate_final_price_greedy_selection():
    c1 = MockCoupon(amount=10.0, condition_amount=50.0)
    c2 = MockCoupon(amount=20.0, condition_amount=50.0)
    sku = MockSKU(price=100.0, coupons=[c1, c2])
    result = PromotionService.calculate_final_price(sku)
    # Service picks the largest coupon (20.0)
    assert result["final_price"] == 80.0
    assert result["total_discount"] == 20.0

def test_calculate_final_price_filters_expired_coupon():
    now = datetime.now(timezone.utc)
    expired_coupon = MockCoupon(
        amount=10.0, 
        start_time=now - timedelta(days=5),
        end_time=now - timedelta(days=1)
    )
    sku = MockSKU(price=100.0, coupons=[expired_coupon])
    result = PromotionService.calculate_final_price(sku)
    assert result["final_price"] == 100.0
    assert result["total_discount"] == 0.0

def test_calculate_final_price_filters_future_coupon():
    now = datetime.now(timezone.utc)
    future_coupon = MockCoupon(
        amount=30.0, 
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=5)
    )
    sku = MockSKU(price=100.0, coupons=[future_coupon])
    result = PromotionService.calculate_final_price(sku)
    assert result["final_price"] == 100.0
    assert result["total_discount"] == 0.0

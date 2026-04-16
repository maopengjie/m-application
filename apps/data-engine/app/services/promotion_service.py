from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any
from app.schemas.product import Coupon, ProductSKU

class PromotionService:
    @staticmethod
    def calculate_final_price(sku: ProductSKU) -> Dict[str, Any]:
        """
        Calculate the final price after all applicable promotions.
        Returns a dict with final_price and promotion_details.
        """
        base_price = Decimal(str(sku.price))
        final_price = base_price
        promotions = []
        
        now = datetime.now(timezone.utc)

        def is_coupon_valid(c):
            # Check price threshold
            if c.condition_amount is not None and base_price < c.condition_amount:
                return False
            
            # Check time validity
            # Handle naive datetime conversions safely if needed
            c_start = c.start_time.replace(tzinfo=timezone.utc) if c.start_time and c.start_time.tzinfo is None else c.start_time
            c_end = c.end_time.replace(tzinfo=timezone.utc) if c.end_time and c.end_time.tzinfo is None else c.end_time
            
            if c_start and now < c_start:
                return False
            if c_end and now > c_end:
                return False
                
            return True

        # Assuming coupons are sorted by amount descending for simple greedy calculation
        applicable_coupons = sorted(
            [c for c in sku.coupons if is_coupon_valid(c)],
            key=lambda x: x.amount,
            reverse=True
        )

        # Apply top 1 coupon for MVP
        if applicable_coupons:
            coupon = applicable_coupons[0]
            final_price -= Decimal(str(coupon.amount))
            promotions.append({
                "type": "COUPON",
                "title": f"优惠券 -¥{coupon.amount}",
                "amount": float(coupon.amount)
            })

        # Ensure price doesn't go below 0
        final_price = max(final_price, Decimal("0.00"))

        return {
            "final_price": float(final_price),
            "promotions": promotions,
            "total_discount": float(base_price - final_price)
        }

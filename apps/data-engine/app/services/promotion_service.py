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

        # Assuming coupons are sorted by amount descending for simple greedy calculation
        # In a real system, this would be much more complex (best combination)
        applicable_coupons = sorted(
            [c for c in sku.coupons if c.condition_amount is None or base_price >= c.condition_amount],
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

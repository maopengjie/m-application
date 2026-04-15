from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.schemas.decision import DecisionResponse


class DecisionService:
    def __init__(self):
        self.product_repo = ProductRepository()

    def get_decision(self, db: Session, sku_id: int) -> DecisionResponse:
        sku = self.product_repo.get_sku_by_id(db, sku_id)
        if not sku:
            return None

        # 1. 价格分 (40%) - Compared to original price
        price_score = 0
        if sku.original_price and sku.original_price > 0:
            discount_rate = (sku.original_price - sku.price) / sku.original_price
            price_score = min(int(discount_rate * 200), 100)  # max 100
        else:
            price_score = 70  # default

        # 2. 历史位置 (30%) - Compared to historical min
        history_score = 80
        if sku.price_history:
            prices = [h.price for h in sku.price_history]
            min_h = min(prices)
            max_h = max(prices)
            if max_h > min_h:
                # Closer to min_h is better
                history_score = int(100 * (max_h - sku.price) / (max_h - min_h))
                history_score = max(0, min(100, history_score))
            elif sku.price <= min_h:
                history_score = 100

        # 3. 优惠 (15%) - Present or not
        coupon_score = 100 if sku.coupons else 50

        # 4. 风险 (15%) - From risk_score
        risk_val = sku.risk_score.score if sku.risk_score else 80
        risk_score = risk_val

        # Total score
        total_score = int(
            price_score * 0.4 + history_score * 0.3 + coupon_score * 0.15 + risk_score * 0.15
        )

        suggestion = "WAIT"
        if total_score > 80:
            suggestion = "BUY"
        elif total_score < 50:
            suggestion = "AVOID"

        reasons = []
        if price_score > 80: reasons.append("当前折扣力度大")
        if history_score > 80: reasons.append("接近历史最低价")
        if coupon_score == 100: reasons.append("有额外优惠券可用")
        if risk_val > 90: reasons.append("商家靠谱，评分高")
        
        reason_str = "、".join(reasons) if reasons else "价格处于平稳期"

        return DecisionResponse(
            sku_id=sku_id,
            score=total_score,
            suggestion=suggestion,
            confidence=0.85,
            reason=reason_str,
            price_score=price_score,
            history_score=history_score,
            coupon_score=coupon_score,
            risk_score=risk_score
        )

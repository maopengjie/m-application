from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.schemas.decision import DecisionResponse
from app.services.promotion_service import PromotionService


class DecisionService:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.promo_service = PromotionService()

    def get_decision(self, db: Session, sku_id: int) -> DecisionResponse:
        sku = self.product_repo.get_sku_by_id(db, sku_id)
        if not sku:
            return None
        
        # Get other SKUs for this product to find best platform
        product = sku.product
        all_skus = product.skus
        
        # Calculate final price for current SKU
        current_promo = self.promo_service.calculate_final_price(sku)
        current_final_price = current_promo["final_price"]

        # 1. 价格分 (40%) - Compared to other platforms and original price
        # Find platform prices
        platform_prices = []
        for s in all_skus:
            p = self.promo_service.calculate_final_price(s)
            platform_prices.append(p["final_price"])
        
        min_platform_price = min(platform_prices) if platform_prices else current_final_price
        
        # Score based on how close to min platform price and discount from original
        price_competitiveness = 100 if current_final_price <= min_platform_price else int(100 * min_platform_price / current_final_price)
        
        discount_rate = 0
        if sku.original_price and sku.original_price > 0:
            discount_rate = (float(sku.original_price) - current_final_price) / float(sku.original_price)
        
        discount_score = min(int(discount_rate * 250), 100) # 20% discount = 50 points, 40% = 100 points
        
        price_score = int(price_competitiveness * 0.6 + discount_score * 0.4)

        # 2. 历史位置 (30%) - Compared to 90-day stats
        history_score = 70
        history_stats = self.product_repo.get_price_history_with_stats(db, sku_id, days=90)
        h_min = history_stats["min_price"]
        h_max = history_stats["max_price"]
        
        if h_max > h_min:
            # Score 100 if current price is at or below historical min
            # Score 0 if current price is at historical max
            history_score = int(100 * (h_max - current_final_price) / (h_max - h_min))
            history_score = max(0, min(100, history_score))
        elif current_final_price <= h_min:
            history_score = 100

        # 3. 优惠 (15%) - Promotion strength
        coupon_benefit = current_promo["total_discount"]
        coupon_score = min(int((coupon_benefit / current_final_price) * 500), 100) if current_final_price > 0 else 50
        if not sku.coupons and coupon_score < 50: coupon_score = 30 # No coupons penalty

        # 4. 风险 (15%) - From risk_score
        risk_val = sku.risk_score.score if sku.risk_score else 50
        risk_score = risk_val

        # Total weighted score
        total_score = int(
            price_score * 0.4 + history_score * 0.3 + coupon_score * 0.15 + risk_score * 0.15
        )

        # Best platform info
        best_sku = sku
        lowest_seen_price = current_final_price
        for s in all_skus:
            p = self.promo_service.calculate_final_price(s)
            if p["final_price"] < lowest_seen_price:
                best_sku = s
                lowest_seen_price = p["final_price"]
        
        best_platform = f"{best_sku.platform} ({best_sku.shop_name})"

        suggestion = "WAIT"
        confidence = 0.7 + (total_score / 1000)
        if total_score > 80:
            suggestion = "BUY"
        elif total_score < 50:
            suggestion = "AVOID"

        reasons = []
        if current_final_price <= float(h_min) * 1.02: 
            reasons.append("当前处于历史极低价区间")
        elif current_final_price >= float(h_max) * 0.8:
            reasons.append("当前价格处于相对高位")
            
        if price_competitiveness >= 95: reasons.append("全网价格最优")
        elif price_competitiveness < 80: reasons.append("其他平台有更低报价")
        
        if discount_rate >= 0.2: reasons.append(f"折扣力度大({int(discount_rate*100)}%)")
        
        if risk_val >= 90: reasons.append("商家信誉极高")
        elif risk_val < 60: reasons.append("该商家存在一定风险")
        
        if not reasons:
            if total_score > 60: reasons.append("价格较稳，可按需入手")
            else: reasons.append("建议继续观察，等待更优折扣")
        
        reason_str = "；".join(reasons)

        return DecisionResponse(
            sku_id=sku_id,
            score=total_score,
            suggestion=suggestion,
            confidence=round(confidence, 2),
            reason=reason_str,
            price_score=price_score,
            history_score=history_score,
            coupon_score=coupon_score,
            risk_score=risk_score,
            best_platform=best_platform
        )

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

        # Calculate price difference from historical min
        price_diff = float(current_final_price) - float(h_min)
        price_diff_percent = (price_diff / float(h_min) * 100) if float(h_min) > 0 else 0

        # Extract evidence and risks
        evidences = []
        risks = []
        
        # Evidence Logic
        if price_diff <= 0:
            evidences.append("当前处于历史最低价格，具备极强的购买价值")
        elif price_diff_percent < 5:
            evidences.append(f"当前价格贴近史低价，仅高出 ¥{price_diff:.0f} ({price_diff_percent:.1f}%)")
        
        if price_competitiveness >= 98:
            evidences.append("已对全网 5 个主流平台进行比价，当前渠道到手价最省")
        elif discount_rate >= 0.2:
            evidences.append(f"到手价较建议零售价已大幅下浮 {int(discount_rate*100)}%，折扣力度显著")

        if sku.is_official and risk_val >= 80:
            evidences.append("货源来自官方自营/旗舰店，综合售后评价极佳")

        # Risk Logic
        if not sku.is_official:
            risks.append("当前最低价来自第三方店铺，建议仔细甄别售后保障及店铺资质")
        
        if price_diff_percent > 15:
            risks.append(f"当前价格相比历史低点溢价达 {price_diff_percent:.0f}%，价格处于相对高位")
        
        if risk_val < 85: # Increased threshold for risk explanation
            if sku.risk_score:
                if sku.risk_score.comment_abnormal:
                    risks.append("AI 语义分析识别到该商品近期评价中‘质量、发货’相关负面词汇增多，可能存在品控风险")
                if sku.risk_score.price_abnormal:
                    risks.append("检测到价格存在异常跳变，警惕商家先涨后降或大数据杀熟行为")
                if sku.risk_score.sales_abnormal:
                    risks.append("销量走势与行业均值背离，可能存在虚假交易或清仓处理情况")
                if sku.risk_score.rating_low:
                    risks.append("商家综合评分显著低于同品类平均水平，售后服务保障性较低")
            elif risk_val < 65:
                risks.append("该渠道近期综合动态评分有所下滑，建议核实后再下单")

        # Map action logic (Requirement 4.1: Conclusion + Action)
        if suggestion == "BUY":
            action_label = "前往平台立即下单"
            action_type = "NAV_BUY"
        elif suggestion == "WAIT":
            action_label = "设置降价提醒，等待好价"
            action_type = "SET_ALERT"
        else:
            action_label = "查看同类替代商品"
            action_type = "NAV_SEARCH"

        # Build discount breakdown
        discount_details = [f"初始价格: ¥{sku.price:.2f}"]
        for promo in current_promo.get("promotions", []):
            discount_details.append(f"{promo['title']}")
        
        return DecisionResponse(
            sku_id=sku_id,
            score=total_score,
            suggestion=suggestion,
            confidence=round(confidence, 2),
            reason=evidences[0] if evidences else (risks[0] if risks else "建议继续观察"),
            price_score=price_score,
            history_score=history_score,
            coupon_score=coupon_score,
            risk_score=risk_score,
            best_platform=best_platform,
            evidence_text="；".join(evidences[:3]) if evidences else None,
            evidence_delta_percent=round(price_diff_percent, 1),
            risk_text=" ; ".join(risks[:3]) if risks else None,
            action_label=action_label,
            action_type=action_type,
            # R1-01 & R1-04
            original_price=float(sku.price),
            final_price=current_final_price,
            total_discount=current_promo["total_discount"],
            discount_details=discount_details
        )

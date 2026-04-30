import json
import logging
from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from typing import List, Optional, Any
from app.core.redis import get_redis_client


from app.services.promotion_service import PromotionService


class ProductService:
    def __init__(self):
        self.repo = ProductRepository()
        self.promo_service = PromotionService()
        self.redis = get_redis_client()
        self.logger = logging.getLogger(__name__)

    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        products = db.query(Product).offset(skip).limit(limit).all()
        for product in products:
            all_prices = []
            all_final_prices = []
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
                
                all_prices.append(float(sku.price))
                all_final_prices.append(float(sku.final_price))
            
            if all_prices:
                product.min_price = min(all_prices)
                product.final_price = min(all_final_prices)
            else:
                product.min_price = 0.0
                product.final_price = 0.0
                
        return products

    def get_product(self, db: Session, product_id: int) -> Any:
        cache_key = f"product:{product_id}"
        
        # 1. Try to get from cache
        try:
            cached = self.redis.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for product:{product_id}")
                from app.schemas.product import Product as ProductSchema
                # Re-validate and return the Pydantic model directly to ensure parity
                return ProductSchema.model_validate_json(cached)
        except Exception as e:
            self.logger.warning(f"Redis read error: {e}")

        # 2. Cache miss, fetch from DB
        product = self.repo.get_by_id(db, product_id)
        if product:
            # Attach computed fields (Promotions, etc.)
            all_prices = []
            all_final_prices = []
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
                
                all_prices.append(float(sku.price))
                all_final_prices.append(float(sku.final_price))
            
            if all_prices:
                product.min_price = min(all_prices)
                product.final_price = min(all_final_prices)
            else:
                product.min_price = 0.0
                product.final_price = 0.0
            
            # 3. Save to cache
            try:
                from app.schemas.product import Product as ProductSchema
                # Convert ORM to Pydantic and then to JSON-serializable dict
                pydantic_product = ProductSchema.model_validate(product)
                self.redis.setex(cache_key, 3600, pydantic_product.model_dump_json())
                self.logger.info(f"Cache write for product:{product_id}")
                return pydantic_product
            except Exception as e:
                self.logger.warning(f"Redis write error: {e}")
            
        return product

    def search_products(
        self, 
        db: Session, 
        query: str, 
        limit: int = 20, 
        skip: int = 0, 
        category: str = None, 
        brand: str = None,
        min_price: float = None,
        max_price: float = None,
        platforms: List[str] = None,
        sort_by: str = None
    ):
        results, total_count = self.repo.search(
            db, 
            query, 
            limit=limit, 
            skip=skip, 
            category=category, 
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            platforms=platforms,
            sort_by=sort_by
        )
        # Results is List[tuple[Product, float]], we need to attach final_price to SKUs
        for product, _ in results:
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
        return results, total_count

    def create_product(self, db: Session, product_in: dict) -> Product:
        db_product = Product(**product_in)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product

    def delete_product(self, db: Session, product_id: int) -> bool:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if db_product:
            db.delete(db_product)
            db.commit()
            
            # Evict cache to maintain consistency
            try:
                self.redis.delete(f"product:{product_id}")
                self.logger.info(f"Cache evicted for product:{product_id}")
            except Exception as e:
                self.logger.warning(f"Redis delete error during product eviction: {e}")
                
            return True
        return False

    def get_price_history(self, db: Session, sku_id: int, days: int = 30):
        return self.repo.get_price_history_with_stats(db, sku_id, days)

    def get_alternatives(self, db: Session, product_id: int, limit: int = 5) -> List[Product]:
        products = self.repo.get_alternatives(db, product_id, limit)
        for product in products:
            all_prices = []
            all_final_prices = []
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
                
                all_prices.append(float(sku.price))
                all_final_prices.append(float(sku.final_price))
            
            if all_prices:
                product.min_price = min(all_prices)
                product.final_price = min(all_final_prices)
            else:
                product.min_price = 0.0
                product.final_price = 0.0
                
        return products

    def follow_product(self, db: Session, user_id: int, product_id: int):
        return self.repo.follow_product(db, user_id, product_id)

    def unfollow_product(self, db: Session, user_id: int, product_id: int) -> bool:
        return self.repo.unfollow_product(db, user_id, product_id)

    def list_followed_products(self, db: Session, user_id: int):
        follows = self.repo.list_followed_products(db, user_id)
        for follow in follows:
            product = follow.product
            all_prices = []
            all_final_prices = []
            
            # Find the best SKU to show metrics for
            best_sku = None
            min_final_price = float('inf')
            
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
                
                all_prices.append(float(sku.price))
                all_final_prices.append(float(sku.final_price))
                
                if sku.final_price < min_final_price:
                    min_final_price = sku.final_price
                    best_sku = sku
            
            if all_prices:
                product.min_price = min(all_prices)
                product.final_price = min(all_final_prices)
            
            # Populate metrics (F2-05)
            if best_sku:
                # 1. Price Change
                if best_sku.price_history:
                    sorted_history = sorted(best_sku.price_history, key=lambda x: x.recorded_at)
                    start_price = float(sorted_history[0].price)
                    current_price = float(best_sku.final_price)
                    follow.price_change_percent = ((current_price - start_price) / start_price * 100) if start_price else 0
                    
                    # 2. Is Near Low
                    hist_min = min([float(h.price) for h in best_sku.price_history] + [current_price])
                    follow.is_near_low = current_price <= (hist_min * 1.05) 
                
                # 3. Risk Status
                if best_sku.risk_score:
                    score = best_sku.risk_score.score
                    if score < 40: follow.risk_status = "高风险"
                    elif score < 70: follow.risk_status = "警告"
                    else: follow.risk_status = "安全"
                else:
                    follow.risk_status = "正常"
                
                # 4. Status Text
                if follow.is_near_low:
                    follow.current_status_text = "捕捉到历史低点"
                elif follow.price_change_percent and follow.price_change_percent < -5:
                    follow.current_status_text = f"较观察期下调 {abs(follow.price_change_percent):.0f}%"
                elif follow.risk_status != "安全" and follow.risk_status != "正常":
                    follow.current_status_text = "检测到品质/评分风险"
                else:
                    follow.current_status_text = "价格趋势平稳"
                    
        return follows


    def get_product_detail(self, db: Session, product_id: int, user_id: int):
        product = self.get_product(db, product_id)
        is_followed = self.repo.is_followed(db, user_id, product_id)
        
        # Check if alert is set
        from app.models.product import PriceAlert, ProductSKU
        from sqlalchemy import and_
        active_alerts = (
            db.query(PriceAlert)
            .join(ProductSKU)
            .filter(
                and_(
                    ProductSKU.product_id == product_id,
                    PriceAlert.user_id == user_id,
                    PriceAlert.status == "monitoring"
                )
            )
            .all()
        )
        
        # Generate Revisit Summary (D2-03)
        revisit_summary = None
        if is_followed or active_alerts:
            # Look for recent changes
            best_sku = None
            min_price = float('inf')
            for sku in product.skus:
                if sku.final_price and sku.final_price < min_price:
                    min_price = sku.final_price
                    best_sku = sku
            
            if best_sku and best_sku.price_history:
                # Compare current price with history
                hist = sorted(best_sku.price_history, key=lambda x: x.recorded_at)
                first_price = float(hist[0].price)
                current_price = float(best_sku.final_price)
                
                # Logic: Is it hitting target?
                hitting_target = any(current_price <= float(a.target_price) for a in active_alerts)
                
                if hitting_target:
                    revisit_summary = {
                        "title": "已达到目标价",
                        "content": f"当前价格 ¥{current_price} 已命中您的监测点，建议立即下单。",
                        "type": "success",
                        "icon": "lucide:sparkles"
                    }
                elif current_price < first_price * 0.95:
                    revisit_summary = {
                        "title": "监测到降价异动",
                        "content": f"自您关注以来，该商品已累计下调了 ¥{int(first_price - current_price)}（{( (first_price-current_price)/first_price*100 ):.0f}%）。",
                        "type": "success",
                        "icon": "lucide:trending-down"
                    }
                elif best_sku.risk_score and best_sku.risk_score.score < 50:
                    revisit_summary = {
                        "title": "品质风险预警",
                        "content": "近期该商品的商家评分或售后评价出现异常波动，请谨慎下单。",
                        "type": "warning",
                        "icon": "lucide:shield-alert"
                    }
                else:
                    revisit_summary = {
                        "title": "状态追踪中",
                        "content": "价格目前处于平稳区间。我们会持续为您盯盘全网隐藏券与限时活动。",
                        "type": "info",
                        "icon": "lucide:clock"
                    }

        return {
            "product": product,
            "is_followed": is_followed,
            "is_alert_set": len(active_alerts) > 0,
            "active_alert_count": len(active_alerts),
            "revisit_summary": revisit_summary
        }



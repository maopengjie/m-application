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
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
        return products

    def get_product(self, db: Session, product_id: int) -> Any:
        cache_key = f"product:{product_id}"
        
        # 1. Try to get from cache
        try:
            cached = self.redis.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for product:{product_id}")
                return json.loads(cached)
        except Exception as e:
            self.logger.warning(f"Redis read error: {e}")

        # 2. Cache miss, fetch from DB
        product = self.repo.get_by_id(db, product_id)
        if product:
            # Attach computed fields (Promotions, etc.)
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
            
            # 3. Save to cache
            try:
                from app.schemas.product import Product as ProductSchema
                # Convert ORM to Pydantic and then to JSON-serializable dict
                pydantic_product = ProductSchema.model_validate(product)
                self.redis.setex(cache_key, 3600, pydantic_product.model_dump_json())
                self.logger.info(f"Cache write for product:{product_id}")
            except Exception as e:
                self.logger.warning(f"Redis write error: {e}")
            
        return product

    def search_products(self, db: Session, query: str, limit: int = 20, skip: int = 0, category: str = None, brand: str = None):
        results = self.repo.search(db, query, limit=limit, skip=skip, category=category, brand=brand)
        # Results is List[tuple[Product, float]], we need to attach final_price to SKUs
        for product, _ in results:
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
        return results

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
            return True
        return False

    def get_price_history(self, db: Session, sku_id: int, days: int = 30):
        return self.repo.get_price_history_with_stats(db, sku_id, days)

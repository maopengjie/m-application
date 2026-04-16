from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from typing import List, Optional


from app.services.promotion_service import PromotionService


class ProductService:
    def __init__(self):
        self.repo = ProductRepository()
        self.promo_service = PromotionService()

    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        products = db.query(Product).offset(skip).limit(limit).all()
        for product in products:
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
        return products

    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        product = self.repo.get_by_id(db, product_id)
        if product:
            for sku in product.skus:
                promo = self.promo_service.calculate_final_price(sku)
                sku.final_price = promo["final_price"]
                sku.promotions = promo["promotions"]
        return product

    def search_products(self, db: Session, query: str, limit: int = 20):
        results = self.repo.search(db, query, limit)
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

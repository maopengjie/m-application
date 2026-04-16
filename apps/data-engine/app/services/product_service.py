from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from typing import List, Optional


class ProductService:
    def __init__(self):
        self.repo = ProductRepository()

    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        # Reuse existing logic for now or move to repo
        return db.query(Product).offset(skip).limit(limit).all()

    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        return self.repo.get_by_id(db, product_id)

    def search_products(self, db: Session, query: str, limit: int = 20):
        results = self.repo.search(db, query, limit)
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

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app.models.product import Product, ProductSKU
from typing import List, Optional


class ProductRepository:
    def get_by_id(self, db: Session, product_id: int) -> Optional[Product]:
        return (
            db.query(Product)
            .options(
                joinedload(Product.skus).joinedload(ProductSKU.price_history),
                joinedload(Product.skus).joinedload(ProductSKU.coupons),
                joinedload(Product.skus).joinedload(ProductSKU.reviews),
                joinedload(Product.skus).joinedload(ProductSKU.risk_score),
            )
            .filter(Product.id == product_id)
            .first()
        )

    def search(self, db: Session, query: str, limit: int = 20) -> List[tuple[Product, float]]:
        # Simple DB search fallback
        search_filter = or_(
            Product.name.ilike(f"%{query}%"),
            Product.brand.ilike(f"%{query}%"),
            Product.category.ilike(f"%{query}%"),
        )
        products = db.query(Product).filter(search_filter).limit(limit).all()
        
        results = []
        for p in products:
            # Find min price for this product
            min_price = db.query(func.min(ProductSKU.price)).filter(ProductSKU.product_id == p.id).scalar()
            results.append((p, float(min_price) if min_price else 0.0))
        
        return results

    def get_sku_by_id(self, db: Session, sku_id: int) -> Optional[ProductSKU]:
        return (
            db.query(ProductSKU)
            .options(
                joinedload(ProductSKU.price_history),
                joinedload(ProductSKU.coupons),
                joinedload(ProductSKU.risk_score),
            )
            .filter(ProductSKU.id == sku_id)
            .first()
        )

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

    def search(self, db: Session, query: str, limit: int = 20, skip: int = 0, category: str = None, brand: str = None) -> List[tuple[Product, float]]:
        # Simple DB search fallback
        q = db.query(Product)
        
        # Keyword search
        search_filter = or_(
            Product.name.ilike(f"%{query}%"),
            Product.brand.ilike(f"%{query}%"),
            Product.category.ilike(f"%{query}%"),
        )
        q = q.filter(search_filter)
        
        # Precise filters
        if category:
            q = q.filter(Product.category == category)
        if brand:
            q = q.filter(Product.brand == brand)
            
        products = q.offset(skip).limit(limit).all()
        
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

    def get_price_history_with_stats(self, db: Session, sku_id: int, days: int = 30) -> dict:
        from datetime import datetime, timedelta
        from app.models.product import PriceHistory

        start_date = datetime.now() - timedelta(days=days)
        history = (
            db.query(PriceHistory)
            .filter(PriceHistory.sku_id == sku_id, PriceHistory.recorded_at >= start_date)
            .order_by(PriceHistory.recorded_at.asc())
            .all()
        )

        if not history:
            # Fallback to get last known price if no history in range
            sku = db.query(ProductSKU).filter(ProductSKU.id == sku_id).first()
            current_price = float(sku.price) if sku else 0.0
            return {
                "history": [],
                "min_price": current_price,
                "max_price": current_price,
                "avg_price": current_price,
                "current_price": current_price,
            }

        prices = [float(h.price) for h in history]
        current_price = prices[-1]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        return {
            "history": [{"price": h.price, "recorded_at": h.recorded_at} for h in history],
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": avg_price,
            "current_price": current_price,
        }

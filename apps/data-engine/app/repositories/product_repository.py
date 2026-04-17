from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_, select, case
from app.models.product import Product, ProductSKU, Coupon
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

    def search(
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
    ) -> tuple[List[tuple[Product, float]], int]:
        # Calculate maximum applicable coupon dynamically per SKU
        discount_subq = (
            select(func.max(Coupon.amount))
            .where(
                Coupon.sku_id == ProductSKU.id,
                or_(
                    Coupon.condition_amount.is_(None),
                    ProductSKU.price >= Coupon.condition_amount
                ),
                or_(
                    Coupon.start_time.is_(None),
                    Coupon.start_time <= func.now()
                ),
                or_(
                    Coupon.end_time.is_(None),
                    Coupon.end_time >= func.now()
                )
            )
            .correlate(ProductSKU)
            .scalar_subquery()
        )
        
        # Calculate effective price, ensuring it doesn't drop below 0
        discount = func.coalesce(discount_subq, 0)
        effective_price = case(
            (ProductSKU.price - discount < 0, 0),
            else_=ProductSKU.price - discount
        )

        # Query product and the minimum effective price among its matched SKUs
        q = (
            db.query(Product, func.min(effective_price).label("min_p"))
            .join(ProductSKU)
            .options(
                selectinload(Product.skus).selectinload(ProductSKU.coupons),
                selectinload(Product.skus).selectinload(ProductSKU.reviews)
            )
        )

        # Keyword search with word splitting for better matching
        keywords = query.split()
        if keywords:
            keyword_filters = []
            for word in keywords:
                keyword_filters.append(
                    or_(
                        Product.name.ilike(f"%{word}%"),
                        Product.brand.ilike(f"%{word}%"),
                        Product.category.ilike(f"%{word}%"),
                    )
                )
            q = q.filter(*keyword_filters)

        # Precise filters on Product
        if category:
            q = q.filter(Product.category == category)
        if brand:
            q = q.filter(Product.brand == brand)

        # Filters on ProductSKU
        if min_price is not None:
            q = q.filter(ProductSKU.price >= min_price)
        if max_price is not None:
            q = q.filter(ProductSKU.price <= max_price)
        if platforms:
            q = q.filter(ProductSKU.platform.in_(platforms))

        # Group by product ID so we aggregate SKUs per product
        q = q.group_by(Product.id)
        
        # Calculate TOTAL matched elements before applying limit/offset
        total_count = q.count()

        # Apply global SQL sorting BEFORE pagination
        if sort_by == "price_asc":
            q = q.order_by(func.min(effective_price).asc())
        elif sort_by == "price_desc":
            q = q.order_by(func.min(effective_price).desc())

        # Paginate the globally sorted and filtered result
        products_with_prices = q.offset(skip).limit(limit).all()

        results = []
        for p, min_p in products_with_prices:
            results.append((p, float(min_p) if min_p else 0.0))
        
        return results, total_count

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

import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.product import ProductSKU, PriceHistory
from app.repositories.product_repository import ProductRepository


class CollectorService:
    def __init__(self):
        self.repo = ProductRepository()

    def simulate_price_collection(self, db: Session):
        """
        Simulate a collection run:
        1. Fetch all active SKUs.
        2. Generate a new price with slight fluctuation (-2% to +2%).
        3. Update SKU current price.
        4. Record new price in history.
        """
        skus = db.query(ProductSKU).all()
        updates_count = 0
        
        for sku in skus:
            old_price = float(sku.price)
            # Simulate fluctuation
            fluctuation = random.uniform(-0.02, 0.02)
            new_price = round(old_price * (1 + fluctuation), 2)
            
            # Update current price
            sku.price = new_price
            sku.updated_at = datetime.now()
            
            # Record in history
            history = PriceHistory(
                sku_id=sku.id,
                price=new_price,
                recorded_at=datetime.now()
            )
            db.add(history)
            updates_count += 1
            
        db.commit()
        print(f"[{datetime.now()}] CollectorService: Updated {updates_count} SKU prices.")
        return updates_count

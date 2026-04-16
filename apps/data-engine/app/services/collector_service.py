import random
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.product import ProductSKU, PriceHistory
from app.models.task import CrawlTask
from app.repositories.product_repository import ProductRepository
from app.services.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

class CollectorService:
    def __init__(self):
        self.repo = ProductRepository()
        self.base_scraper = BaseScraper()

    def run_collection(self, db: Session):
        """
        Main collection entry point.
        """
        task = CrawlTask(
            task_type="price_update",
            status="running",
            start_time=datetime.now()
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            skus = db.query(ProductSKU).all()
            task.total_count = len(skus)
            
            success_count = 0
            failed_count = 0
            errors = []

            for sku in skus:
                try:
                    # In a real system, we'd have platform-specific URLs in the model
                    # For now, we simulate the "scraping" outcome for different platforms
                    new_price = self._scrape_sku_price(sku)
                    
                    if new_price:
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
                        success_count += 1
                    else:
                        raise Exception(f"Failed to fetch price for {sku.platform}")
                        
                except Exception as e:
                    failed_count += 1
                    errors.append(f"SKU {sku.id} ({sku.platform}) error: {str(e)}")

            task.success_count = success_count
            task.failed_count = failed_count
            task.status = "success" if failed_count == 0 else "partial_success"
            if errors:
                task.error_log = "\n".join(errors[:10])
            
            task.end_time = datetime.now()
            db.commit()
            
            logger.info(f"CollectorService Run: {success_count} success, {failed_count} failed. Task ID: {task.id}")
            return success_count

        except Exception as e:
            task.status = "failed"
            task.error_log = str(e)
            task.end_time = datetime.now()
            db.commit()
            logger.error(f"CollectorService Task {task.id} CRITICAL FAILURE: {e}")
            raise e

    def _scrape_sku_price(self, sku: ProductSKU) -> Optional[float]:
        """
        Specialized logic for different platforms.
        Currently handles simulated fetch with network logic.
        """
        # Simulate network fetch for the 'true crawler' experience
        # In the future, this will call JDScraper / TmallScraper
        # random.uniform(0.1, 0.5) delay is already in BaseScraper.fetch_url
        
        # We simulate a 95% success rate to show error handling
        if random.random() < 0.05:
            return None
            
        old_price = float(sku.price)
        fluctuation = random.uniform(-0.015, 0.015)
        new_price = round(old_price * (1 + fluctuation), 2)
        
        return new_price

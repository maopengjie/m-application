from app.core.database import SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_mock_data():
    db = SessionLocal()
    # Ordered by dependency to avoid FK violations
    tables = [
        "price_history", 
        "product_reviews", 
        "risk_scores", 
        "coupons",
        "product_skus",
        "products",
        "crawl_tasks",
        "platform_health_metrics",
        "scraper_alerts"
    ]
    
    try:
        # Disable foreign key checks for clean truncation if necessary
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        for table in tables:
            try:
                db.execute(text(f"DELETE FROM {table}"))
                logger.info(f"Successfully cleared table: {table}")
            except Exception as e:
                logger.error(f"Failed to clear table {table}: {e}")
        
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        logger.info("Database cleanup completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Critical failure during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clear_mock_data()

from sqlalchemy import create_engine, text
from app.core.config import get_settings

def migrate():
    settings = get_settings()
    engine = create_engine(settings.mysql_dsn)
    
    with engine.connect() as conn:
        print("Starting migration...")
        try:
            conn.execute(text("ALTER TABLE product_skus ADD COLUMN buy_url VARCHAR(500)"))
            print("Added buy_url to product_skus")
        except Exception as e:
            print(f"buy_url Error: {e}")
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN rating DECIMAL(3,1) DEFAULT 4.5"))
            print("Added rating to products")
        except Exception as e:
            print(f"rating Error: {e}")
            
        try:
            conn.execute(text("ALTER TABLE risk_scores ADD COLUMN price_abnormal BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE risk_scores ADD COLUMN rating_low BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE risk_scores ADD COLUMN details_json TEXT"))
            print("Added new risk columns")
        except Exception as e:
            print(f"Risk columns Error: {e}")
            
        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()

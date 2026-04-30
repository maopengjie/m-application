import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from elasticsearch import Elasticsearch
from app.core.elasticsearch import get_es_client
from app.models.product import Product, ProductSKU

logger = logging.getLogger(__name__)

class SearchService:
    MONITOR_INDEX = "price_monitors"
    PRODUCT_INDEX = "products"

    def __init__(self, client: Elasticsearch | None = None):
        self.client = client or get_es_client()

    def is_enabled(self) -> bool:
        return self.client is not None

    def ensure_product_index(self) -> bool:
        if self.client is None: return False
        try:
            if self.client.indices.exists(index=self.PRODUCT_INDEX):
                return True
            self.client.indices.create(
                index=self.PRODUCT_INDEX,
                mappings={
                    "properties": {
                        "name": {"type": "text"},
                        "brand": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "ai_attributes": {"type": "object"},
                        "skus": {
                            "type": "nested",
                            "properties": {
                                "platform": {"type": "keyword"},
                                "price": {"type": "float"},
                                "title": {"type": "text"}
                            }
                        },
                        "updated_at": {"type": "date"}
                    }
                },
            )
            return True
        except Exception as e:
            logger.error(f"ES product index creation failed: {e}")
            return False

    def index_product(self, product: Product) -> bool:
        if self.client is None: return False
        try:
            self.ensure_product_index()
            sku_data = [
                {"platform": s.platform, "price": float(s.price), "title": s.title}
                for s in product.skus
            ]
            
            doc = {
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "ai_attributes": product.ai_attributes or {},
                "skus": sku_data,
                "updated_at": datetime.now().isoformat()
            }
            
            self.client.index(index=self.PRODUCT_INDEX, id=str(product.id), document=doc, refresh=True)
            return True
        except Exception as e:
            logger.error(f"ES indexing failed for product {product.id}: {e}")
            return False

    def search_products(self, query_text: str, filters: Dict = None, limit: int = 20) -> List[Dict]:
        if self.client is None: return []
        try:
            self.ensure_product_index()
            
            must_clauses = [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["name^5", "brand^2", "category", "ai_attributes.*"]
                    }
                }
            ]
            
            if filters:
                for k, v in filters.items():
                    must_clauses.append({"match": {f"ai_attributes.{k}": v}})

            response = self.client.search(
                index=self.PRODUCT_INDEX,
                size=limit,
                query={"bool": {"must": must_clauses}}
            )
            
            return [{**hit["_source"], "score": hit["_score"]} for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"ES search failed: {e}")
            return []

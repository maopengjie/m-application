from elasticsearch import Elasticsearch

from app.core.elasticsearch import get_es_client
from app.models.price_monitor import PriceMonitor


class SearchService:
    INDEX_NAME = "price_monitors"

    def __init__(self, client: Elasticsearch | None = None):
        self.client = client or get_es_client()

    def is_enabled(self) -> bool:
        return self.client is not None

    def ensure_index(self) -> bool:
        if self.client is None:
            return False
        if self.client.indices.exists(index=self.INDEX_NAME):
            return True
        self.client.indices.create(
            index=self.INDEX_NAME,
            mappings={
                "properties": {
                    "name": {"type": "text"},
                    "platform": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "target_price": {"type": "float"},
                    "current_price": {"type": "float"},
                }
            },
        )
        return True

    def index_monitor(self, monitor: PriceMonitor) -> bool:
        if self.client is None:
            return False
        self.ensure_index()
        self.client.index(
            index=self.INDEX_NAME,
            id=str(monitor.id),
            document={
                "id": monitor.id,
                "name": monitor.name,
                "url": monitor.url,
                "platform": monitor.platform,
                "status": monitor.status,
                "target_price": monitor.target_price,
                "current_price": monitor.current_price,
            },
            refresh=True,
        )
        return True

    def search_monitors(self, query: str, limit: int = 20) -> list[dict]:
        if self.client is None:
            return []
        self.ensure_index()
        response = self.client.search(
            index=self.INDEX_NAME,
            size=limit,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "platform", "status"],
                }
            },
        )
        return [
            {
                "id": int(hit["_id"]),
                "score": hit["_score"],
                **hit["_source"],
            }
            for hit in response["hits"]["hits"]
        ]

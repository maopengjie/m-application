import json
import random
from collections.abc import Sequence

from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.redis import get_redis_client
from app.models.price_monitor import PriceMonitor
from app.repositories.price_monitor_repository import PriceMonitorRepository
from app.services.search_service import SearchService


class PriceMonitorService:
    CACHE_KEY = "price_monitors:list"
    CACHE_TTL_SECONDS = 300

    def __init__(self, repository: PriceMonitorRepository | None = None):
        self.repository = repository or PriceMonitorRepository()
        self.redis = get_redis_client()
        self.search_service = SearchService()

    def list_monitors(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[PriceMonitor]:
        cache_key = f"{self.CACHE_KEY}:{skip}:{limit}"
        try:
            cached = self.redis.get(cache_key)
            if cached:
                items = json.loads(cached)
                return [PriceMonitor(**item) for item in items]
        except RedisError:
            cached = None
        monitors = self.repository.list(db, skip=skip, limit=limit)
        try:
            self.redis.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps([self._serialize_monitor(item) for item in monitors]),
            )
        except RedisError:
            pass
        return monitors

    def create_monitor(self, db: Session, payload: dict) -> PriceMonitor:
        monitor = self.repository.create(db, payload)
        self._clear_list_cache()
        self.search_service.index_monitor(monitor)
        return monitor

    def update_all_prices(self, db: Session) -> None:
        monitors = self.repository.list(db, skip=0, limit=1_000)
        for monitor in monitors:
            if monitor.status != "active":
                continue
            monitor.current_price = round(random.uniform(10.0, 500.0), 2)
            monitor = self.repository.save(db, monitor)
            self.search_service.index_monitor(monitor)
        self._clear_list_cache()

    @staticmethod
    def _serialize_monitor(monitor: PriceMonitor) -> dict:
        return {
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "target_price": monitor.target_price,
            "current_price": monitor.current_price,
            "platform": monitor.platform,
            "status": monitor.status,
            "created_at": monitor.created_at.isoformat() if monitor.created_at else None,
            "updated_at": monitor.updated_at.isoformat() if monitor.updated_at else None,
        }

    def _clear_list_cache(self) -> None:
        try:
            for key in self.redis.scan_iter(f"{self.CACHE_KEY}:*"):
                self.redis.delete(key)
        except RedisError:
            pass

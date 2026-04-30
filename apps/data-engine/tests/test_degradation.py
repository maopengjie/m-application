import pytest
from unittest.mock import MagicMock
from redis.exceptions import RedisError
from sqlalchemy.orm import Session
from app.services.product_service import ProductService
from app.services.price_service import PriceMonitorService
from app.models.product import Product
from app.models.price_monitor import PriceMonitor

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def product_data():
    from datetime import datetime
    return Product(
        id=1, 
        name="Fail Test Product", 
        brand="Test", 
        category="Test", 
        skus=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def monitor_data():
    from datetime import datetime
    return PriceMonitor(
        id=101, 
        name="Fail Monitor", 
        url="http://test.com", 
        target_price=50.0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def test_product_service_redis_read_failure_degradation(mock_db, product_data):
    # Setup
    service = ProductService()
    mock_redis = MagicMock()
    mock_redis.get.side_effect = RedisError("Redis is down")
    service.redis = mock_redis
    
    service.repo.get_by_id = MagicMock(return_value=product_data)
    
    # Execute - should not raise exception
    result = service.get_product(mock_db, 1)
    
    # Verify
    assert result.id == 1
    assert service.repo.get_by_id.called
    # Logs should have a warning (verified by inspection or log capturing if needed)


def test_product_service_redis_write_failure_degradation(mock_db, product_data):
    # Setup
    service = ProductService()
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.setex.side_effect = RedisError("Redis write failed")
    service.redis = mock_redis
    
    service.repo.get_by_id = MagicMock(return_value=product_data)
    
    # Execute - should not raise exception
    result = service.get_product(mock_db, 1)
    
    # Verify
    assert result.id == 1
    assert mock_redis.setex.called


def test_price_service_redis_scan_failure_degradation(mock_db):
    service = PriceMonitorService()
    mock_redis = MagicMock()
    mock_redis.scan_iter.side_effect = RedisError("Redis scan failed")
    service.redis = mock_redis
    
    # Execute - should not raise
    service._clear_list_cache()
    
    # Verify
    assert mock_redis.scan_iter.called


def test_price_service_elasticsearch_indexing_failure_degradation(mock_db, monitor_data):
    service = PriceMonitorService()
    
    # Mock Repository
    service.repository.create = MagicMock(return_value=monitor_data)
    
    # Mock Search Service to fail
    service.search_service.index_monitor = MagicMock(side_effect=Exception("ES Connection Refused"))
    
    # Execute - should not raise, allowing creation to succeed
    result = service.create_monitor(mock_db, {"name": "Test"})
    
    # Verify
    assert result.id == 101
    assert service.search_service.index_monitor.called


def test_price_service_elasticsearch_bulk_update_failure_degradation(mock_db, monitor_data):
    service = PriceMonitorService()
    
    # Mock Repository
    monitor_data.status = "active"
    service.repository.list = MagicMock(return_value=[monitor_data])
    service.repository.save = MagicMock(return_value=monitor_data)
    
    # Mock Search Service to fail
    service.search_service.index_monitor = MagicMock(side_effect=Exception("ES Timeout"))
    
    # Execute - should not raise
    service.update_all_prices(mock_db)
    
    # Verify
    assert service.search_service.index_monitor.called
    assert service.repository.save.called


def test_search_service_elasticsearch_search_failure_degradation():
    from app.services.search_service import SearchService
    
    # Setup SearchService with a mocked client
    mock_client = MagicMock()
    service = SearchService(client=mock_client)
    
    # Mock search to fail
    mock_client.search.side_effect = Exception("Elasticsearch Cluster Down")
    mock_client.indices.exists.return_value = True
    
    # Execute - should return empty list instead of raising
    results = service.search_monitors(query="test")
    
    # Verify
    assert results == []
    assert mock_client.search.called


def test_price_monitor_service_redis_read_failure_degradation(mock_db, monitor_data):
    service = PriceMonitorService()
    mock_redis = MagicMock()
    mock_redis.get.side_effect = RedisError("Redis unavailable for price list")
    service.redis = mock_redis
    
    # Mock Repository result
    service.repository.list = MagicMock(return_value=[monitor_data])
    
    # Execute - should fallback to DB
    results = service.list_monitors(mock_db)
    
    # Verify
    assert len(results) == 1
    assert results[0].id == 101
    assert service.repository.list.called


def test_price_monitor_service_redis_write_failure_degradation(mock_db, monitor_data):
    service = PriceMonitorService()
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.setex.side_effect = RedisError("Redis cache write failed")
    service.redis = mock_redis
    
    # Mock Repository result
    service.repository.list = MagicMock(return_value=[monitor_data])
    
    # Execute - should complete via DB and suppress Redis write error
    results = service.list_monitors(mock_db)
    
    # Verify
    assert len(results) == 1
    assert mock_redis.setex.called
    assert service.repository.list.called

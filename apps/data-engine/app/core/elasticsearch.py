from functools import lru_cache

from elasticsearch import AsyncElasticsearch, Elasticsearch

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_es_client() -> Elasticsearch | None:
    settings = get_settings()
    if not settings.enable_elasticsearch:
        return None
    return Elasticsearch(settings.elasticsearch_url)


@lru_cache(maxsize=1)
def get_async_es_client() -> AsyncElasticsearch | None:
    settings = get_settings()
    if not settings.enable_elasticsearch:
        return None
    return AsyncElasticsearch(settings.elasticsearch_url)


async def close_es_client():
    client = get_async_es_client()
    if client is not None:
        await client.close()

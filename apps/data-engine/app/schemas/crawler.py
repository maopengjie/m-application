from pydantic import BaseModel


class CrawlerStartPayload(BaseModel):
    target_url: str

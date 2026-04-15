from pydantic import BaseModel


class CrawlerStartPayload(BaseModel):
    target_url: str


class CrawlPreviewPayload(BaseModel):
    target_url: str
    selector: str | None = None
    dynamic: bool = False

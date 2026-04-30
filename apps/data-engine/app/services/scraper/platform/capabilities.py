from pydantic import BaseModel
from typing import List, Dict, Optional

class PlatformCapability(BaseModel):
    """
    Defines the technical behavior and data coverage for a specific platform.
    """
    platform_code: str
    supported_fields: List[str] = ["price", "title"] # Minimum default
    browser_fallback_supported: bool = True
    requires_proxy: bool = False
    default_request_interval: float = 1.0
    concurrency_limit: int = 1

PLATFORM_CAPABILITIES: Dict[str, PlatformCapability] = {
    "JD": PlatformCapability(
        platform_code="JD",
        supported_fields=["price", "title", "shop_name", "original_price", "stock_status"],
        browser_fallback_supported=True,
        requires_proxy=True, # JD blocks easily
        default_request_interval=2.0,
        concurrency_limit=1
    ),
    "Tmall": PlatformCapability(
        platform_code="Tmall",
        supported_fields=["price", "title", "shop_name", "stock_status"],
        browser_fallback_supported=True,
        requires_proxy=True,
        default_request_interval=3.0,
        concurrency_limit=1
    ),
    "PDD": PlatformCapability(
        platform_code="PDD",
        supported_fields=["price", "title"], # PDD is harder to get full info from
        browser_fallback_supported=True,
        requires_proxy=True,
        default_request_interval=5.0,
        concurrency_limit=1
    ),
    "MOCK": PlatformCapability(
        platform_code="MOCK",
        supported_fields=["price", "title", "shop_name", "stock_status", "original_price"],
        browser_fallback_supported=False,
        requires_proxy=False,
        default_request_interval=0.1,
        concurrency_limit=5
    )
}

def get_platform_capability(platform: str) -> PlatformCapability:
    """Returns the capability profile for a given platform."""
    return PLATFORM_CAPABILITIES.get(platform.upper(), PLATFORM_CAPABILITIES["MOCK"])

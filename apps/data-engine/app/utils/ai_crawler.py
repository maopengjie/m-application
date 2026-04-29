import asyncio
import logging
from typing import Optional, Dict, Any, List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy

logger = logging.getLogger(__name__)

class AIWebCrawler:
    """
    Advanced Web Crawler powered by Crawl4AI.
    Provides AI-ready data extraction, Markdown conversion, and structured output.
    """

    @staticmethod
    async def crawl(
        url: str,
        extraction_strategy: Optional[Any] = None,
        bypass_cache: bool = True,
        css_selector: Optional[str] = None,
        wait_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crawls a URL and returns structured data.
        """
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS if bypass_cache else CacheMode.ENABLED,
            extraction_strategy=extraction_strategy,
            css_selector=css_selector,
            wait_for=wait_for,
            word_count_threshold=10,
            excluded_tags=['nav', 'footer', 'script', 'style'],
            remove_overlay_elements=True,
            process_iframes=True
        )

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if not result.success:
                logger.error(f"Crawl failed for {url}: {result.error_message}")
                return {"success": False, "error": result.error_message}

            return {
                "success": True,
                "url": url,
                "markdown": result.markdown,
                "cleaned_html": result.cleaned_html,
                "extracted_content": result.extracted_content,
                "media": result.media,
                "links": result.links,
                "metadata": result.metadata,
                "screenshot": result.screenshot
            }

    @classmethod
    async def extract_structured_data(
        cls, 
        url: str, 
        schema: Dict[str, Any],
        base_selector: str
    ) -> Dict[str, Any]:
        """
        Extracts structured JSON data using a CSS schema.
        """
        strategy = JsonCssExtractionStrategy(schema, base_selector=base_selector)
        return await cls.crawl(url, extraction_strategy=strategy)

    @classmethod
    async def extract_with_llm(
        cls,
        url: str,
        instruction: str,
        provider: str = "openai/gpt-4o",
        api_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts information using an LLM provider.
        """
        strategy = LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,
            instruction=instruction
        )
        return await cls.crawl(url, extraction_strategy=strategy)

def crawl_url_sync(url: str, **kwargs) -> Dict[str, Any]:
    """Synchronous wrapper for AIWebCrawler.crawl."""
    return asyncio.run(AIWebCrawler.crawl(url, **kwargs))

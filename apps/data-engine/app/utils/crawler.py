import asyncio
from typing import Optional

from playwright.async_api import async_playwright
import httpx


async def get_page_content_httpx(url: str) -> str:
    """Fetch content using httpx (fast, for static pages)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

async def get_page_content_playwright(url: str, selector: Optional[str] = None) -> str:
    """Fetch content using playwright (for dynamic pages)."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        if selector:
            await page.wait_for_selector(selector)
        content = await page.content()
        await browser.close()
        return content


def fetch_page_content(url: str, selector: Optional[str] = None, use_playwright: bool = False) -> str:
    if use_playwright:
        return asyncio.run(get_page_content_playwright(url, selector))
    return asyncio.run(get_page_content_httpx(url))

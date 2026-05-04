import time
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests import Response

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional runtime dependency
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None

from celery_app import app

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db.session import SessionLocal, init_db  # noqa: E402
from services import ingest_sku_payload  # noqa: E402


TAG_RULES = [
    ("京东自营", "JD_SELF_OPERATED", "SYSTEM"),
    ("百亿补贴", "HUNDRED_BILLION_SUBSIDY", "RULE"),
    ("PLUS专享", "PLUS_EXCLUSIVE", "RULE"),
]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def _extract_sku_id(url: str) -> str | None:
    match = re.search(r"/(\d+)\.html", url)
    if match:
        return match.group(1)
    query_match = re.search(r"sku(?:Id)?=(\d+)", url, re.IGNORECASE)
    if query_match:
        return query_match.group(1)
    return None


def _extract_title(soup: BeautifulSoup) -> str | None:
    selectors = [
        "#name h1",
        ".sku-name",
        "meta[property='og:title']",
        "title",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue
        if node.name == "meta":
            return _clean_text(node.get("content"))
        return _clean_text(node.get_text(" ", strip=True))
    return None


def _extract_image(soup: BeautifulSoup) -> str | None:
    selectors = [
        "meta[property='og:image']",
        "#spec-img",
        ".jqzoom img",
        "#J_imgBooth",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue
        if node.name == "meta":
            return _clean_text(node.get("content"))
        for attr in ("data-origin", "data-url", "src"):
            value = _clean_text(node.get(attr))
            if value:
                return value
    return None


def _extract_brand(soup: BeautifulSoup, product_name: str | None) -> str | None:
    brand_selectors = [
        "#parameter-brand a",
        ".p-parameter .brand a",
        ".crumb .item a[clstag*='shangpin']",
    ]
    for selector in brand_selectors:
        node = soup.select_one(selector)
        if node:
            text = _clean_text(node.get_text(" ", strip=True))
            if text:
                return text

    if not product_name:
        return None
    first_token = _clean_text(product_name.split(" ")[0])
    return first_token


def _extract_categories(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    texts: list[str] = []
    for node in soup.select(".crumb a, .breadcrumb a, .p-parameter .detail-tab-main a"):
        text = _clean_text(node.get_text(" ", strip=True))
        if text and text not in texts and "首页" not in text:
            texts.append(text)
    if len(texts) >= 3:
        return texts[0], texts[1], texts[2]
    return (
        texts[0] if len(texts) > 0 else None,
        texts[1] if len(texts) > 1 else None,
        texts[2] if len(texts) > 2 else None,
    )


def _extract_shop_name(soup: BeautifulSoup) -> str | None:
    selectors = [
        ".shopName",
        ".name a",
        ".J-hove-wrap .shop-name",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = _clean_text(node.get_text(" ", strip=True))
            if text:
                return text
    return None


def _extract_attributes(soup: BeautifulSoup) -> list[dict[str, str | None]]:
    attrs: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()

    for item in soup.select("ul.parameter2 li, ul.p-parameter-list li"):
        text = _clean_text(item.get_text(" ", strip=True))
        if not text or "：" not in text:
            continue
        name, value = [part.strip() for part in text.split("：", 1)]
        key = (name, value)
        if key in seen:
            continue
        seen.add(key)
        attrs.append(
            {
                "attr_group": "主体",
                "attr_name": name,
                "attr_value": value,
                "attr_unit": None,
                "source_text": text,
            }
        )

    current_group = None
    for row in soup.select("table.Ptable tr, .Ptable-item dl"):
        if row.name == "tr":
            if row.get("class") and any("Ptable-item-head" in cls for cls in row.get("class", [])):
                current_group = _clean_text(row.get_text(" ", strip=True))
                continue
            th = row.select_one("th")
            td = row.select_one("td")
            if not th or not td:
                continue
            name = _clean_text(th.get_text(" ", strip=True))
            value = _clean_text(td.get_text(" ", strip=True))
        else:
            dt = row.select_one("dt")
            dd = row.select_one("dd")
            if not dt or not dd:
                continue
            name = _clean_text(dt.get_text(" ", strip=True))
            value = _clean_text(dd.get_text(" ", strip=True))
        if not name or not value:
            continue
        key = (name, value)
        if key in seen:
            continue
        seen.add(key)
        attrs.append(
            {
                "attr_group": current_group or "规格",
                "attr_name": name,
                "attr_value": value,
                "attr_unit": None,
                "source_text": f"{name}: {value}",
            }
        )
    return attrs


def _extract_tags(html: str, shop_name: str | None) -> list[dict[str, str]]:
    haystack = " ".join(filter(None, [html, shop_name]))
    tags: list[dict[str, str]] = []
    for keyword, code, tag_type in TAG_RULES:
        if keyword in haystack:
            tags.append(
                {
                    "tag_code": code,
                    "tag_name": keyword,
                    "tag_type": tag_type,
                    "source_type": "AUTO",
                }
            )
    return tags


def _parse_product_payload(url: str, html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    parsed_url = urlparse(url)
    platform = "jd" if "jd.com" in parsed_url.netloc else parsed_url.netloc or "unknown"
    product_name = _extract_title(soup)
    category_level_1, category_level_2, category_level_3 = _extract_categories(soup)
    shop_name = _extract_shop_name(soup)

    return {
        "platform": platform,
        "sku_id": _extract_sku_id(url),
        "product_name": product_name,
        "normalized_name": product_name,
        "brand_name": _extract_brand(soup, product_name),
        "main_image_url": _extract_image(soup),
        "category_level_1": category_level_1,
        "category_level_2": category_level_2,
        "category_level_3": category_level_3,
        "shop_name": shop_name,
        "product_url": url,
        "status": 1,
        "attributes": _extract_attributes(soup),
        "tags": _extract_tags(html, shop_name),
    }


def _payload_quality(payload: dict[str, object]) -> int:
    score = 0
    if payload.get("sku_id"):
        score += 2
    if payload.get("product_name"):
        score += 3
    if payload.get("brand_name"):
        score += 1
    if payload.get("main_image_url"):
        score += 1
    if payload.get("shop_name"):
        score += 1
    score += min(len(payload.get("attributes") or []), 6)
    score += min(len(payload.get("tags") or []), 3)
    categories = [
        payload.get("category_level_1"),
        payload.get("category_level_2"),
        payload.get("category_level_3"),
    ]
    score += len([item for item in categories if item])
    return score


def _needs_browser_fallback(payload: dict[str, object]) -> bool:
    if not payload.get("product_name"):
        return True
    if len(payload.get("attributes") or []) < 2:
        return True
    if not payload.get("main_image_url"):
        return True
    return False


def _fetch_html_with_requests(url: str) -> tuple[dict[str, object], Response]:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
    response.raise_for_status()
    return _parse_product_payload(url, response.text), response


def _fetch_html_with_playwright(url: str) -> tuple[dict[str, object], str]:
    if sync_playwright is None:
        raise RuntimeError("Playwright is not installed in the worker environment")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="zh-CN",
            viewport={"width": 1440, "height": 2200},
        )
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector(
                    ".sku-name, #name h1, ul.parameter2, table.Ptable, .Ptable-item",
                    timeout=12000,
                )
            except PlaywrightTimeoutError:
                pass
            page.wait_for_timeout(2000)
            html = page.content()
            return _parse_product_payload(url, html), html
        finally:
            page.close()
            browser.close()


def _persist_payload(payload: dict[str, object]) -> dict[str, object]:
    init_db()
    db = SessionLocal()
    try:
        return ingest_sku_payload(db, payload)
    finally:
        db.close()

@app.task(name="tasks.scraping.test_task")
def test_task(name: str):
    print(f"Starting test task for {name}")
    time.sleep(2)
    return f"Hello, {name}! Task completed."


@app.task(name="tasks.scraping.ingest_product_payload")
def ingest_product_payload(payload: dict):
    result = _persist_payload(payload)
    return {"status": "success", "result": result}


@app.task(name="tasks.scraping.scrape_product")
def scrape_product(url: str):
    print(f"Scraping product from {url}")
    strategy = "requests"
    payload, response = _fetch_html_with_requests(url)
    fallback_reason = None

    if _needs_browser_fallback(payload):
        fallback_reason = (
            f"weak static payload: score={_payload_quality(payload)}, "
            f"attributes={len(payload.get('attributes') or [])}"
        )
        try:
            browser_payload, _ = _fetch_html_with_playwright(url)
            if _payload_quality(browser_payload) >= _payload_quality(payload):
                payload = browser_payload
                strategy = "playwright"
        except Exception as exc:
            fallback_reason = f"{fallback_reason}; playwright_error={exc}"

    result = _persist_payload(payload)
    return {
        "status": "success",
        "url": url,
        "data": payload,
        "result": result,
        "meta": {
            "fallback_reason": fallback_reason,
            "http_status": response.status_code,
            "strategy": strategy,
        },
    }

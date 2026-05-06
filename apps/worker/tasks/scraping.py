import time
import re
import sys
from datetime import datetime
import json
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
from models import AnomalyAlert, CategoryNode, ScrapeTaskRun, SkuProduct  # noqa: E402
from services.anomaly_recovery import resolve_recovered_data_anomalies  # noqa: E402
from services import ingest_sku_payload  # noqa: E402
from services.task_runs import mark_stale_scrape_runs  # noqa: E402


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

JD_CATEGORY_TREE_URL = "https://www.jd.com/allSort.aspx"


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


def _price_yuan_to_cents(value: str | int | float | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-1", "-1.00"}:
        return None
    match = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    return int(round(float(match.group(0)) * 100))


def _amount_yuan_to_cents(value: str) -> int:
    return int(round(float(value.replace(",", "")) * 100))


def _collect_promo_texts(soup: BeautifulSoup) -> list[str]:
    selectors = [
        "#summary-promotion",
        ".summary-promotion",
        ".J-prom",
        ".prom-item",
        "#summary-quan",
        ".summary-quan",
        ".quan-item",
        ".plus-price",
        ".summary-top",
    ]
    texts: list[str] = []
    seen: set[str] = set()
    for selector in selectors:
        for node in soup.select(selector):
            text = _clean_text(node.get_text(" ", strip=True))
            if not text:
                continue
            if not re.search(r"满|减|券|补贴|PLUS|plus|直降|立减|秒杀|优惠", text, re.IGNORECASE):
                continue
            if text in seen:
                continue
            seen.add(text)
            texts.append(text)
    return texts[:8]


def _sum_promo_amounts(texts: list[str], patterns: list[str]) -> int:
    total = 0
    matched_values: set[tuple[str, str]] = set()
    for text in texts:
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                raw_amount = match.group(1)
                key = (pattern, raw_amount)
                if key in matched_values:
                    continue
                matched_values.add(key)
                total += _amount_yuan_to_cents(raw_amount)
    return total


def _cap_promotion_amounts(
    *,
    coupon_amount: int,
    final_price: int,
    list_price: int,
    other_discount_amount: int,
    reduction_amount: int,
) -> tuple[int, int, int, int]:
    total_discount = reduction_amount + coupon_amount + other_discount_amount
    if total_discount <= 0:
        return list_price, reduction_amount, coupon_amount, other_discount_amount

    if list_price <= final_price:
        list_price = final_price + total_discount

    price_gap = max(list_price - final_price, 0)
    if price_gap <= 0 or total_discount <= price_gap:
        return list_price, reduction_amount, coupon_amount, other_discount_amount

    ratio = price_gap / total_discount
    reduction_amount = int(round(reduction_amount * ratio))
    coupon_amount = int(round(coupon_amount * ratio))
    other_discount_amount = max(price_gap - reduction_amount - coupon_amount, 0)
    return list_price, reduction_amount, coupon_amount, other_discount_amount


def _extract_promotion_model(soup: BeautifulSoup, snapshot: dict[str, object]) -> dict[str, object]:
    texts = _collect_promo_texts(soup)
    if not texts:
        return snapshot

    reduction_amount = _sum_promo_amounts(
        texts,
        [
            r"满\s*\d+(?:\.\d+)?\s*减\s*(\d+(?:\.\d+)?)",
            r"(?<!券)(?:立减|直降|每满\s*\d+(?:\.\d+)?\s*减)\s*(\d+(?:\.\d+)?)",
        ],
    )
    coupon_amount = _sum_promo_amounts(
        texts,
        [
            r"(?:券|优惠券|领券|用券|PLUS\s*券|plus\s*券)[^\d]{0,8}(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*元?\s*(?:券|优惠券)",
        ],
    )
    other_discount_amount = _sum_promo_amounts(
        texts,
        [
            r"(?:百亿补贴|平台补贴|补贴|PLUS\s*专享|plus\s*专享|秒杀)[^\d]{0,8}(\d+(?:\.\d+)?)",
        ],
    )
    final_price = int(snapshot.get("final_price") or 0)
    list_price = int(snapshot.get("list_price") or final_price)
    list_price, reduction_amount, coupon_amount, other_discount_amount = _cap_promotion_amounts(
        coupon_amount=coupon_amount,
        final_price=final_price,
        list_price=list_price,
        other_discount_amount=other_discount_amount,
        reduction_amount=reduction_amount,
    )

    if reduction_amount or coupon_amount or other_discount_amount:
        snapshot["list_price"] = list_price
        snapshot["reduction_amount"] = reduction_amount
        snapshot["coupon_amount"] = coupon_amount
        snapshot["other_discount_amount"] = other_discount_amount

    promo_text = "；".join(texts)
    existing_promo = _clean_text(str(snapshot.get("promo_text") or ""))
    snapshot["promo_text"] = f"{existing_promo}；{promo_text}" if existing_promo else promo_text
    return snapshot


def _extract_inline_price_snapshot(soup: BeautifulSoup) -> dict[str, object] | None:
    selectors = [
        ".p-price .price",
        ".p-price .J-p-",
        ".summary-price .price",
        "[class*='price']",
        "meta[property='product:price:amount']",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue
        raw_value = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
        price = _price_yuan_to_cents(raw_value)
        if price is None:
            continue
        return {
            "captured_at": datetime.utcnow().isoformat(timespec="seconds"),
            "final_price": price,
            "list_price": price,
            "promo_text": "页面价格",
        }
    return None


def _fetch_jd_price_snapshot(sku_id: str) -> tuple[dict[str, object] | None, dict[str, object]]:
    started_at = time.perf_counter()
    status_code = 0
    try:
        response = requests.get(
            "https://p.3.cn/prices/mgets",
            headers=DEFAULT_HEADERS,
            params={
                "skuIds": f"J_{sku_id}",
                "type": "1",
            },
            timeout=10,
        )
        status_code = response.status_code
        response.raise_for_status()
        rows = response.json()
        item = rows[0] if isinstance(rows, list) and rows else {}
        final_price = _price_yuan_to_cents(item.get("p"))
        list_price = _price_yuan_to_cents(item.get("m")) or final_price
        if final_price is None:
            return None, {
                "response_time_ms": round((time.perf_counter() - started_at) * 1000),
                "status_code": status_code,
                "target_api": "p.3.cn/prices/mgets",
            }
        return {
            "captured_at": datetime.utcnow().isoformat(timespec="seconds"),
            "final_price": final_price,
            "list_price": list_price or final_price,
            "promo_text": "京东实时价",
        }, {
            "response_time_ms": round((time.perf_counter() - started_at) * 1000),
            "status_code": status_code,
            "target_api": "p.3.cn/prices/mgets",
        }
    except Exception:
        return None, {
            "response_time_ms": round((time.perf_counter() - started_at) * 1000),
            "status_code": status_code or 599,
            "target_api": "p.3.cn/prices/mgets",
        }


def _parse_product_payload(url: str, html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    parsed_url = urlparse(url)
    platform = "jd" if "jd.com" in parsed_url.netloc else parsed_url.netloc or "unknown"
    product_name = _extract_title(soup)
    category_level_1, category_level_2, category_level_3 = _extract_categories(soup)
    shop_name = _extract_shop_name(soup)
    sku_id = _extract_sku_id(url)
    price_snapshot = _extract_inline_price_snapshot(soup)
    efficiency = None
    if platform == "jd" and sku_id:
        jd_snapshot, efficiency = _fetch_jd_price_snapshot(sku_id)
        if jd_snapshot:
            price_snapshot = jd_snapshot
    if price_snapshot:
        price_snapshot = _extract_promotion_model(soup, price_snapshot)

    return {
        "platform": platform,
        "sku_id": sku_id,
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
        "prices": [price_snapshot] if price_snapshot else [],
        "efficiency": efficiency,
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


def _normalize_category_name(value: str | None) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    text = re.sub(r"[>/｜|]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _category_external_id_from_href(href: str | None) -> str | None:
    if not href:
        return None
    for pattern in (
        r"cat=(\d+(?:,\d+)*)",
        r"ev=.*?cid_(\d+)",
        r"/list\.jd\.com/list\.html\?cat=(\d+(?:,\d+)*)",
        r"(\d+)-0-0\.html",
    ):
        match = re.search(pattern, href)
        if match:
            return match.group(1).split(",")[-1]
    return None


def _category_node_from_anchor(anchor) -> dict[str, object] | None:
    name = _normalize_category_name(anchor.get_text(" ", strip=True))
    if not name:
        return None
    return {
        "children": [],
        "external_id": _category_external_id_from_href(anchor.get("href")),
        "name": name,
        "sort_order": 0,
    }


def _parse_jd_category_tree(html: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    roots: list[dict[str, object]] = []
    seen_roots: set[str] = set()

    for item in soup.select(".category-item, .items, .item, dl"):
        root_anchor = item.select_one("dt a, h3 a, .mt a, .item-title a, a")
        if root_anchor is None:
            continue
        root = _category_node_from_anchor(root_anchor)
        if root is None:
            continue
        root_name = str(root["name"])
        if root_name in seen_roots:
            continue

        second_level_nodes: list[dict[str, object]] = []
        seen_second: set[str] = set()
        groups = item.select("dd dl, .mc dl, .subitems dl, .items dl")
        if not groups:
            groups = item.select("dd, .mc, .subitems")

        for group in groups:
            second_anchor = group.select_one("dt a, h4 a, .fore1 a, a")
            if second_anchor is None or second_anchor is root_anchor:
                continue
            second = _category_node_from_anchor(second_anchor)
            if second is None:
                continue
            second_name = str(second["name"])
            if second_name in seen_second or second_name == root_name:
                continue
            seen_second.add(second_name)

            children: list[dict[str, object]] = []
            seen_third: set[str] = set()
            for anchor in group.select("dd a, .items a, a"):
                if anchor is second_anchor or anchor is root_anchor:
                    continue
                third = _category_node_from_anchor(anchor)
                if third is None:
                    continue
                third_name = str(third["name"])
                if third_name in seen_third or third_name in {root_name, second_name}:
                    continue
                seen_third.add(third_name)
                third["sort_order"] = len(children)
                children.append(third)

            second["children"] = children
            second["sort_order"] = len(second_level_nodes)
            second_level_nodes.append(second)

        if not second_level_nodes:
            anchors = item.select("a")
            for anchor in anchors[1:]:
                second = _category_node_from_anchor(anchor)
                if second is None:
                    continue
                second_name = str(second["name"])
                if second_name in seen_second or second_name == root_name:
                    continue
                seen_second.add(second_name)
                second["sort_order"] = len(second_level_nodes)
                second_level_nodes.append(second)

        root["children"] = second_level_nodes
        root["sort_order"] = len(roots)
        roots.append(root)
        seen_roots.add(root_name)

    return roots


def _insert_category_nodes(
    db,
    *,
    level: int,
    nodes: list[dict[str, object]],
    parent_id: int | None,
    parent_path: str,
    platform: str,
) -> int:
    count = 0
    for index, item in enumerate(nodes):
        if level > 3:
            continue
        name = _normalize_category_name(str(item.get("name") or ""))
        if not name:
            continue
        node = CategoryNode(
            platform=platform,
            external_id=_clean_text(item.get("external_id")),
            name=name,
            level=level,
            parent_id=parent_id,
            sort_order=int(item.get("sort_order") or index),
        )
        db.add(node)
        db.flush()
        node.path = f"{parent_path}/{node.id}" if parent_path else str(node.id)
        count += 1
        children = item.get("children") if isinstance(item.get("children"), list) else []
        count += _insert_category_nodes(
            db,
            level=level + 1,
            nodes=children,
            parent_id=node.id,
            parent_path=node.path,
            platform=platform,
        )
    return count


def _replace_category_tree(platform: str, nodes: list[dict[str, object]]) -> int:
    init_db()
    db = SessionLocal()
    try:
        db.query(CategoryNode).filter(CategoryNode.platform == platform).delete()
        count = _insert_category_nodes(
            db,
            level=1,
            nodes=nodes,
            parent_id=None,
            parent_path="",
            platform=platform,
        )
        db.commit()
        return count
    finally:
        db.close()


def _persist_payload(payload: dict[str, object]) -> dict[str, object]:
    init_db()
    db = SessionLocal()
    try:
        return ingest_sku_payload(db, payload)
    finally:
        db.close()


def _update_run_status(
    run_id: int | None,
    *,
    status: str,
    processed_count: int | None = None,
    success_count: int | None = None,
    failure_count: int | None = None,
    summary_message: str | None = None,
    error_message: str | None = None,
    failed_items: list[dict[str, object]] | None = None,
    started: bool = False,
    finished: bool = False,
) -> None:
    if run_id is None:
        return

    init_db()
    db = SessionLocal()
    try:
        run = db.query(ScrapeTaskRun).filter(ScrapeTaskRun.id == run_id).first()
        if run is None:
            return
        run.status = status
        if processed_count is not None:
            run.processed_count = processed_count
        if success_count is not None:
            run.success_count = success_count
        if failure_count is not None:
            run.failure_count = failure_count
        if summary_message is not None:
            run.summary_message = summary_message
        if error_message is not None:
            run.error_message = error_message
        if failed_items is not None:
            run.failed_items_json = json.dumps(failed_items, ensure_ascii=False)
        if started and run.started_at is None:
            run.started_at = datetime.now()
        if finished:
            run.finished_at = datetime.now()
        db.commit()
    finally:
        db.close()


def _create_run_record(
    *,
    task_name: str,
    trigger_source: str,
    platform: str | None = None,
    requested_limit: int | None = None,
    requested_url: str | None = None,
) -> int:
    init_db()
    db = SessionLocal()
    try:
        run = ScrapeTaskRun(
            task_name=task_name,
            trigger_source=trigger_source,
            platform=platform,
            requested_limit=requested_limit,
            requested_url=requested_url,
            status="PENDING",
            summary_message="任务已由 worker 接收",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id
    finally:
        db.close()


def _load_products_for_scrape(limit: int, platform: str | None = None) -> list[tuple[int, str, str]]:
    init_db()
    db = SessionLocal()
    try:
        query = (
            db.query(SkuProduct.id, SkuProduct.platform, SkuProduct.product_url)
            .filter(
                SkuProduct.status == 1,
                SkuProduct.product_url.isnot(None),
                SkuProduct.product_url != "",
            )
            .order_by(SkuProduct.updated_at.asc(), SkuProduct.id.asc())
        )
        if platform:
            query = query.filter(SkuProduct.platform == platform)
        rows = query.limit(limit).all()
        return [(row.id, row.platform, row.product_url) for row in rows if row.product_url]
    finally:
        db.close()


def _record_scrape_failure_anomaly(
    *,
    error_message: str,
    platform: str | None,
    product_id: int | None = None,
    product_url: str | None = None,
) -> None:
    init_db()
    db = SessionLocal()
    try:
        product = None
        if product_id is not None:
            product = db.query(SkuProduct).filter(SkuProduct.id == product_id).first()
        elif product_url:
            product = db.query(SkuProduct).filter(SkuProduct.product_url == product_url).first()

        resolved_platform = platform or (product.platform if product else "unknown")
        resolved_sku_id = (
            product.sku_id
            if product
            else (_extract_sku_id(product_url or "") or "unknown")
        )
        existing = (
            db.query(AnomalyAlert)
            .filter(
                AnomalyAlert.alert_type == "SCRAPE_FAILURE",
                AnomalyAlert.platform == resolved_platform,
                AnomalyAlert.sku_id == resolved_sku_id,
                AnomalyAlert.is_verified == 0,
            )
            .order_by(AnomalyAlert.created_at.desc(), AnomalyAlert.id.desc())
            .first()
        )
        message = f"抓取任务失败：{error_message[:240]}"
        if existing is not None:
            existing.alert_value = product_url or resolved_sku_id
            existing.threshold = "worker scrape"
            existing.message = message
            existing.product_id = product.id if product else None
        else:
            db.add(
                AnomalyAlert(
                    alert_type="SCRAPE_FAILURE",
                    platform=resolved_platform,
                    sku_id=resolved_sku_id,
                    product_id=product.id if product else None,
                    alert_value=product_url or resolved_sku_id,
                    threshold="worker scrape",
                    is_verified=0,
                    message=message,
                )
            )
        db.commit()
    finally:
        db.close()


def _record_data_quality_anomaly(
    *,
    payload: dict[str, object],
    product_url: str,
    quality_score: int,
) -> None:
    init_db()
    db = SessionLocal()
    try:
        platform = str(payload.get("platform") or "unknown")
        sku_id = str(payload.get("sku_id") or _extract_sku_id(product_url) or "unknown")
        product = (
            db.query(SkuProduct)
            .filter(SkuProduct.platform == platform, SkuProduct.sku_id == sku_id)
            .first()
        )
        missing_fields = [
            field
            for field in ("product_name", "main_image_url", "brand_name")
            if not payload.get(field)
        ]
        if len(payload.get("attributes") or []) < 2:
            missing_fields.append("attributes")
        if not payload.get("prices"):
            missing_fields.append("prices")
        message = (
            f"抓取质量偏低 score={quality_score}; "
            f"缺失字段: {', '.join(missing_fields) or 'unknown'}"
        )
        existing = (
            db.query(AnomalyAlert)
            .filter(
                AnomalyAlert.alert_type == "DATA_MISSING",
                AnomalyAlert.platform == platform,
                AnomalyAlert.sku_id == sku_id,
                AnomalyAlert.is_verified == 0,
            )
            .order_by(AnomalyAlert.created_at.desc(), AnomalyAlert.id.desc())
            .first()
        )
        if existing:
            existing.alert_value = product_url
            existing.threshold = "quality_score>=8"
            existing.product_id = product.id if product else None
            existing.message = message
        else:
            db.add(
                AnomalyAlert(
                    alert_type="DATA_MISSING",
                    platform=platform,
                    sku_id=sku_id,
                    product_id=product.id if product else None,
                    alert_value=product_url,
                    threshold="quality_score>=8",
                    is_verified=0,
                    message=message,
                )
            )
        db.commit()
    finally:
        db.close()


def _resolve_recovered_data_anomalies(
    *,
    payload: dict[str, object],
    product_url: str,
    result: dict[str, object],
) -> int:
    init_db()
    db = SessionLocal()
    try:
        platform = str(result.get("platform") or payload.get("platform") or "unknown")
        sku_id = str(result.get("sku_id") or payload.get("sku_id") or _extract_sku_id(product_url) or "unknown")
        product_id = result.get("product_id")
        recovered_count = resolve_recovered_data_anomalies(
            db,
            platform=platform,
            product_id=int(product_id) if product_id else None,
            product_url=product_url,
            sku_id=sku_id,
        )
        if recovered_count:
            db.commit()
        return recovered_count
    finally:
        db.close()


def _scrape_product_once(url: str) -> dict[str, object]:
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
    final_quality = _payload_quality(payload)
    if final_quality < 8:
        _record_data_quality_anomaly(
            payload=payload,
            product_url=url,
            quality_score=final_quality,
        )
        recovered_anomaly_count = 0
    else:
        recovered_anomaly_count = _resolve_recovered_data_anomalies(
            payload=payload,
            product_url=url,
            result=result,
        )
    return {
        "status": "success",
        "url": url,
        "data": payload,
        "result": result,
        "meta": {
            "fallback_reason": fallback_reason,
            "http_status": response.status_code,
            "quality_score": final_quality,
            "recovered_anomaly_count": recovered_anomaly_count,
            "strategy": strategy,
        },
    }

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
def scrape_product(url: str, run_id: int | None = None):
    print(f"Scraping product from {url}")
    if run_id is None:
        run_id = _create_run_record(
            task_name="scrape_product",
            trigger_source="SCHEDULED",
            requested_url=url,
        )
    _update_run_status(
        run_id,
        status="RUNNING",
        started=True,
        summary_message="正在抓取单个商品",
    )
    try:
        result = _scrape_product_once(url)
        recovered_count = int(result.get("meta", {}).get("recovered_anomaly_count") or 0)
        summary_message = "单商品抓取完成"
        if recovered_count:
            summary_message = f"{summary_message}，自动关闭 {recovered_count} 个异常"
        _update_run_status(
            run_id,
            status="SUCCESS",
            processed_count=1,
            success_count=1,
            failure_count=0,
            summary_message=summary_message,
            error_message=None,
            finished=True,
        )
        return result
    except Exception as exc:
        _record_scrape_failure_anomaly(
            error_message=str(exc),
            platform=None,
            product_url=url,
        )
        _update_run_status(
            run_id,
            status="FAILED",
            processed_count=1,
            success_count=0,
            failure_count=1,
            summary_message="单商品抓取失败",
            error_message=str(exc),
            failed_items=[{"error": str(exc), "url": url}],
            finished=True,
        )
        raise


@app.task(name="tasks.scraping.scrape_active_products")
def scrape_active_products(limit: int = 20, platform: str | None = None, run_id: int | None = None):
    if run_id is None:
        run_id = _create_run_record(
            task_name="scrape_active_products",
            trigger_source="SCHEDULED",
            platform=platform,
            requested_limit=limit,
        )
    _update_run_status(
        run_id,
        status="RUNNING",
        started=True,
        summary_message="正在批量抓取在售商品",
    )
    products = _load_products_for_scrape(limit=limit, platform=platform)
    processed = 0
    recovered_total = 0
    succeeded = 0
    failed: list[dict[str, object]] = []

    for product_id, product_platform, product_url in products:
        processed += 1
        try:
            result = _scrape_product_once(product_url)
            recovered_total += int(result.get("meta", {}).get("recovered_anomaly_count") or 0)
            succeeded += 1
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            failure_item = {
                "error": str(exc),
                "platform": product_platform,
                "product_id": product_id,
                "url": product_url,
            }
            failed.append(failure_item)
            _record_scrape_failure_anomaly(
                error_message=str(exc),
                platform=product_platform,
                product_id=product_id,
                product_url=product_url,
            )

    status = "SUCCESS" if not failed else "PARTIAL_SUCCESS"
    summary_message = (
        f"批量抓取完成，成功 {succeeded} 条，失败 {len(failed)} 条"
        if products
        else "当前没有可抓取的在售商品"
    )
    if recovered_total:
        summary_message = f"{summary_message}，自动关闭 {recovered_total} 个异常"
    _update_run_status(
        run_id,
        status=status,
        processed_count=processed,
        success_count=succeeded,
        failure_count=len(failed),
        summary_message=summary_message,
        error_message=failed[0]["error"] if failed else None,
        failed_items=failed[:20],
        finished=True,
    )

    return {
        "status": "success" if not failed else "partial_success",
        "summary": {
            "failed": len(failed),
            "platform": platform,
            "processed": processed,
            "recovered_anomalies": recovered_total,
            "requested_limit": limit,
            "succeeded": succeeded,
        },
        "failed_items": failed,
    }


@app.task(name="tasks.scraping.close_stale_scrape_runs")
def close_stale_scrape_runs():
    init_db()
    db = SessionLocal()
    try:
        closed_count = mark_stale_scrape_runs(db)
        db.commit()
        return {
            "closed_count": closed_count,
            "status": "success",
        }
    finally:
        db.close()


@app.task(name="tasks.scraping.sync_jd_category_tree")
def sync_jd_category_tree(run_id: int | None = None):
    if run_id is None:
        run_id = _create_run_record(
            task_name="sync_jd_category_tree",
            trigger_source="SCHEDULED",
            platform="jd",
            requested_url=JD_CATEGORY_TREE_URL,
        )
    _update_run_status(
        run_id,
        status="RUNNING",
        started=True,
        summary_message="正在同步京东类目树",
    )
    try:
        started_at = time.perf_counter()
        response = requests.get(JD_CATEGORY_TREE_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        nodes = _parse_jd_category_tree(response.text)
        if not nodes:
            raise ValueError("no category nodes parsed from allSort.aspx")
        imported_count = _replace_category_tree("jd", nodes)
        _update_run_status(
            run_id,
            status="SUCCESS",
            processed_count=imported_count,
            success_count=imported_count,
            failure_count=0,
            summary_message=f"京东类目树同步完成，导入 {imported_count} 个节点",
            finished=True,
        )
        return {
            "duration_ms": round((time.perf_counter() - started_at) * 1000),
            "imported_count": imported_count,
            "status": "success",
        }
    except Exception as exc:
        _record_scrape_failure_anomaly(
            error_message=str(exc),
            platform="jd",
            product_url=JD_CATEGORY_TREE_URL,
        )
        _update_run_status(
            run_id,
            status="FAILED",
            processed_count=0,
            success_count=0,
            failure_count=1,
            summary_message="京东类目树同步失败",
            error_message=str(exc),
            failed_items=[{"error": str(exc), "url": JD_CATEGORY_TREE_URL}],
            finished=True,
        )
        raise

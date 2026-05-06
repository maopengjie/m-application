#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta


def request_json(base_url: str, method: str, path: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers={"content-type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {detail}") from exc
    if not raw:
        return {}
    return json.loads(raw)


def unwrap(response: dict) -> object:
    if "code" in response and response.get("code") != 0:
        raise RuntimeError(f"API returned error: {response}")
    return response.get("data", response)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_synthetic_ingest(base_url: str) -> None:
    now = datetime.utcnow()
    sku_id = f"E2E-{now.strftime('%Y%m%d%H%M%S')}"
    payload = {
        "platform": "jd",
        "sku_id": sku_id,
        "product_name": "【验收专用】Apple iPhone 15 Pro Max 256G 黑色 领券立减200",
        "brand_name": "Apple",
        "main_image_url": "https://img14.360buyimg.com/n1/e2e-demo.jpg",
        "category_level_1": "手机通讯",
        "category_level_2": "手机",
        "category_level_3": "智能手机",
        "shop_name": "E2E 京东自营测试店",
        "product_url": f"https://item.jd.com/{sku_id}.html",
        "status": 1,
        "attributes": [
            {"attr_name": "机身内存", "attr_value": "256", "attr_unit": "GB"},
            {"attr_name": "颜色", "attr_value": "黑色"},
            {"attr_name": "处理器", "attr_value": "A17 Pro"},
        ],
        "tags": [
            {"tag_code": "JD_SELF_OPERATED", "tag_name": "京东自营", "tag_type": "SYSTEM"},
            {"tag_code": "PLUS_EXCLUSIVE", "tag_name": "PLUS专享", "tag_type": "RULE"},
        ],
        "prices": [
            {
                "captured_at": (now - timedelta(minutes=20)).isoformat(timespec="seconds"),
                "list_price": 999900,
                "reduction_amount": 50000,
                "coupon_amount": 20000,
                "other_discount_amount": 0,
                "final_price": 929900,
                "promo_text": "满减+券",
            },
            {
                "captured_at": now.isoformat(timespec="seconds"),
                "list_price": 999900,
                "reduction_amount": 50000,
                "coupon_amount": 30000,
                "other_discount_amount": 20000,
                "final_price": 899900,
                "promo_text": "满减+券+补贴",
            },
        ],
        "efficiency": {
            "target_api": "e2e.synthetic",
            "response_time_ms": 123,
            "status_code": 200,
        },
    }

    result = unwrap(request_json(base_url, "POST", "/sku-repository/imports/payload", payload))
    product_id = result["product_id"]
    print(f"ok import sku={sku_id} product_id={product_id}")

    detail = unwrap(request_json(base_url, "GET", f"/sku-repository/products/{product_id}"))
    assert_true(detail["sku_id"] == sku_id, "imported product detail mismatch")
    assert_true(len(detail["attributes"]) >= 3, "attributes were not persisted")
    assert_true(len(detail["tags"]) >= 2, "tags were not persisted")
    print("ok product detail")

    price_detail = unwrap(request_json(base_url, "GET", f"/sku-repository/price-time-series/{product_id}"))
    assert_true(len(price_detail["timeline"]) >= 2, "price timeline missing snapshots")
    assert_true(price_detail["price_extremes"]["lowest_price"] == 8999.0, "lowest price was not recomputed")
    assert_true(len(price_detail["promotion_records"]) >= 2, "promotion records missing")
    print("ok price timeline and promotion model")

    overview = unwrap(request_json(base_url, "GET", "/core-dashboard/overview"))
    assert_true(overview["total_sku_count"] >= 1, "overview SKU count missing")
    assert_true(overview["total_price_records"] >= 2, "overview price count missing")
    print("ok dashboard overview")

    notifications = unwrap(request_json(base_url, "GET", "/data-cleaning/notifications?limit=5"))
    assert_true(isinstance(notifications, list), "notifications endpoint returned non-list")
    print("ok notifications endpoint")


def verify_real_scrape(base_url: str, scrape_url: str, timeout_seconds: int) -> None:
    response = unwrap(
        request_json(
            base_url,
            "POST",
            "/sku-repository/scraping/trigger",
            {"url": scrape_url},
        )
    )
    run_id = response["run"]["id"]
    print(f"ok scrape task submitted run_id={run_id}")
    deadline = time.time() + timeout_seconds
    terminal_statuses = {"SUCCESS", "PARTIAL_SUCCESS", "FAILED"}
    while time.time() < deadline:
        run = unwrap(request_json(base_url, "GET", f"/sku-repository/scraping/runs/{run_id}"))
        status = run["status"]
        if status in terminal_statuses:
            assert_true(status != "FAILED", f"scrape task failed: {run.get('error_message')}")
            assert_true(run["success_count"] >= 1, "scrape task did not report success")
            print(f"ok real scrape completed status={status}")
            return
        time.sleep(3)
    raise TimeoutError(f"scrape task {run_id} did not finish within {timeout_seconds}s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify data-center backend closure.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--scrape-url", default="")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    health = request_json(args.base_url, "GET", "/health")
    assert_true(health.get("status") == "ok", "backend health check failed")
    print("ok backend health")

    verify_synthetic_ingest(args.base_url)
    if args.scrape_url:
        verify_real_scrape(args.base_url, args.scrape_url, args.timeout)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)

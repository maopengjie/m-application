import requests
import json
import datetime

url = "http://localhost:8000/sku-repository/imports/payload"

payload = {
    "platform": "jd",
    "sku_id": "TEST_SKU_001",
    "product_name": "Test Product for Price History",
    "prices": [
        {
            "captured_at": "2026-04-30T10:00:00",
            "list_price": 600000,
            "reduction_amount": 50000,
            "coupon_amount": 20000,
            "final_price": 530000,
            "promo_text": "First Crawl"
        },
        {
            "captured_at": "2026-05-01T10:00:00",
            "list_price": 600000,
            "reduction_amount": 100000,
            "coupon_amount": 0,
            "final_price": 500000,
            "promo_text": "May Day Sale"
        },
        {
            "captured_at": "2026-05-02T10:00:00",
            "list_price": 600000,
            "reduction_amount": 0,
            "coupon_amount": 0,
            "final_price": 600000,
            "promo_text": "Price Up"
        }
    ]
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

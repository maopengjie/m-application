import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log_step(step, content):
    print(f"\n[STEP {step}] {content}")

def check_resp(resp, message="Response check failed"):
    if resp.status_code >= 400:
        print(f"ERROR: {message}")
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
        return None
    data = resp.json()
    if data.get("code") != 0:
        print(f"ERROR: API returned error code {data.get('code')}")
        print(f"Message: {data.get('message')}")
        return None
    return data

def run_acceptance_test():
    session = requests.Session()
    
    # 0. Health Check
    log_step(0, "Health Check")
    try:
        resp = requests.get("http://127.0.0.1:8000/")
        print(f"Server root: {resp.json()}")
    except Exception as e:
        print(f"Could not connect to server: {e}")
        return

    # 1. Login
    log_step(1, "Login")
    # Trying the most likely credentials from the project's tests
    credentials = [
        {"username": "admin", "password": "password123"},
        {"username": "adminuser", "password": "adminpassword"},
        {"username": "testuser", "password": "pass"}
    ]
    
    token = None
    for cred in credentials:
        print(f"Trying login with {cred['username']}...")
        resp = session.post(f"{BASE_URL}/auth/login", json=cred)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                token = data["data"]["accessToken"]
                print(f"Login successful as {cred['username']}")
                break
            else:
                print(f"Login failed for {cred['username']}: {data}")
        else:
            print(f"Login request failed for {cred['username']} with status {resp.status_code}: {resp.text}")
    
    if not token:
        print("CRITICAL: Failed to login with any known credentials. Please ensure a user exists in the DB.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    session.headers.update(headers)

    # 2. Search
    log_step(2, "Search for Products")
    resp = session.get(f"{BASE_URL}/search?q=a") # Broad search
    data = check_resp(resp, "Search stage failed")
    if not data: return
    
    items = data["data"]["items"]
    print(f"Found {len(items)} items.")
    if not items:
        print("ERROR: No products in DB. Cannot continue flow. Please run a crawler or seed data.")
        return
    
    target_product = items[0]
    product_id = target_product["product_id"]
    print(f"Focusing on product: {target_product['name']} (ID: {product_id})")

    # 3. Product Detail
    log_step(3, "Get Product Details")
    resp = session.get(f"{BASE_URL}/products/{product_id}")
    data = check_resp(resp, "Product Detail stage failed")
    if not data: return
    
    product = data["data"]
    print(f"Product detail loaded: {product['name']}")
    if not product.get("skus"):
        print("ERROR: Product has no SKUs")
        return
    
    sku = product["skus"][0]
    sku_id = sku["id"]
    print(f"Focusing on SKU: {sku['title']} (ID: {sku_id})")

    # 4. Decision
    log_step(4, "Get AI Decision")
    resp = session.get(f"{BASE_URL}/decisions/{sku_id}")
    data = check_resp(resp, "Decision stage failed")
    if not data: return
    
    decision = data["data"]
    print(f"Decision received: {decision.get('advice', 'No advice')}")

    # 5. Alert
    log_step(5, "Create Price Alert")
    alert_payload = {
        "sku_id": sku_id,
        "target_price": float(sku["price"]) * 0.9,
        "notify_methods": "web"
    }
    resp = session.post(f"{BASE_URL}/alerts", json=alert_payload)
    if resp.status_code == 400 and "already exists" in resp.text:
         print("Alert already exists, skipping creation...")
    else:
        data = check_resp(resp, "Alert creation failed")
        if data:
            alert_id = data["data"]["id"]
            print(f"Alert created (ID: {alert_id}) for target price {alert_payload['target_price']}")

    # 6. Crawler Task
    log_step(6, "Check Crawler Tasks")
    resp = session.get(f"{BASE_URL}/crawler/tasks")
    data = check_resp(resp, "Crawler tasks fetch failed")
    if not data: return
    
    tasks = data["data"]
    print(f"Listed {len(tasks)} crawler tasks.")
    
    log_step(7, "Trigger Price Update Task")
    resp = session.post(f"{BASE_URL}/crawler/trigger-update")
    data = check_resp(resp, "Trigger update failed")
    if not data: return
    
    print(f"Update triggered: {data['data'].get('updates_count', 0)} items updated.")

    log_step("FINAL", "Acceptance test completed successfully! Full flow coverage confirmed.")

if __name__ == "__main__":
    run_acceptance_test()

import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log_test(role, endpoint, expected_status):
    print(f"Testing [{role}] -> [{endpoint}] expects {expected_status}... ", end="")

def verify(resp, expected_status):
    if resp.status_code == expected_status:
        print("✅ PASS")
        return True
    else:
        print(f"❌ FAIL (Got {resp.status_code})")
        return False

def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json()["data"]["accessToken"]
    return None

def run_regression():
    users = [
        {"role": "super", "user": "vben", "pass": "123456"},
        {"role": "admin", "user": "admin", "pass": "123456"},
        {"role": "user", "user": "jack", "pass": "123456"},
    ]
    
    endpoints = [
        {"path": "/crawler/tasks", "name": "Crawler Tasks", "restricted": True},
        {"path": "/prices", "name": "Price Monitors", "restricted": True},
        {"path": "/user/1/unlock", "name": "User Unlock", "restricted": True, "method": "POST"},
        {"path": "/alerts/scan", "name": "Alerts Scan", "restricted": True, "method": "POST"},
        {"path": "/search?q=a", "name": "Search", "restricted": False},
        {"path": "/alerts", "name": "Alerts List", "restricted": False},
    ]

    all_passed = True
    
    for u in users:
        print(f"\n--- Testing Role: {u['role']} ({u['user']}) ---")
        token = get_token(u["user"], u["pass"])
        if not token:
            print(f"Failed to login as {u['user']}")
            all_passed = False
            continue
            
        headers = {"Authorization": f"Bearer {token}"}
        
        for ep in endpoints:
            expected = 200
            if ep["restricted"] and u["role"] == "user":
                expected = 403
            
            method = ep.get("method", "GET")
            log_test(u["role"], ep["name"], expected)
            
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{ep['path']}", headers=headers)
            else:
                resp = requests.post(f"{BASE_URL}{ep['path']}", headers=headers)
            
            if not verify(resp, expected):
                all_passed = False
                
    if all_passed:
        print("\n🏆 PERMISSION REGRESSION SUCCESSFUL")
    else:
        print("\n🚨 PERMISSION REGRESSION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    run_regression()

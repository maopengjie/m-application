from celery_app import app
import time

@app.task(name="tasks.scraping.test_task")
def test_task(name: str):
    print(f"Starting test task for {name}")
    time.sleep(2)
    return f"Hello, {name}! Task completed."

@app.task(name="tasks.scraping.scrape_product")
def scrape_product(url: str):
    # This will be implemented using Playwright
    print(f"Scraping product from {url}")
    return {"status": "success", "url": url, "data": {}}

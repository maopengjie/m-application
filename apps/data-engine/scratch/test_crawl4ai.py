import asyncio
from app.utils.ai_crawler import AIWebCrawler
import json

async def main():
    url = "https://httpbin.org/html"
    print(f"Crawling {url}...")
    result = await AIWebCrawler.crawl(url)
    
    if result["success"]:
        print("\n--- Markdown Output (First 500 chars) ---")
        print(result["markdown"][:500])
        print("\n--- Metadata ---")
        print(json.dumps(result["metadata"], indent=2))
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())

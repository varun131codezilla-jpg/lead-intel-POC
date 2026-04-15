
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

def debug_full_pipe(domain):
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. ACTUAL MAP TEST
    print(f"--- MAPPING: {domain} ---")
    map_payload = {
        "url": f"https://{domain}",
        "search": "blog insights news careers jobs hiring"
    }
    map_resp = requests.post("https://api.firecrawl.dev/v1/map", headers=headers, json=map_payload, timeout=60)
    links = map_resp.json().get("links", []) if map_resp.status_code == 200 else []
    print(f"Found {len(links)} links")
    
    # Simulate the Hub-Aware logic
    found_urls = {"blog": None, "career": None}
    for item in links:
        url = item.get("url", "").rstrip('/')
        url_lower = url.lower()
        path = url_lower.split(domain)[-1] if domain in url_lower else url_lower
        path_segments = [s for s in path.split('/') if s]
        is_hub = len(path_segments) <= 1
        
        if any(kw in url_lower for kw in ["blog", "insights", "news"]):
            if not found_urls["blog"] or (is_hub and "/" not in found_urls["blog"].split(domain)[-1].strip('/')):
                found_urls["blog"] = url
        if any(kw in url_lower for kw in ["career", "jobs", "hiring"]):
            if not found_urls["career"] or (is_hub and "/" not in found_urls["career"].split(domain)[-1].strip('/')):
                found_urls["career"] = url

    print(f"Discovered Hubs: {found_urls}")

    # 2. ACTUAL SCRAPE TEST
    schema = {
        "type": "object",
        "properties": {
            "signals": {"type": "array", "items": {"type": "string"}},
            "open_roles": {"type": "array", "items": {"type": "string"}},
            "tech_stack": {"type": "array", "items": {"type": "string"}},
            "whitespace_summary": {"type": "string"},
            "confidence_score": {"type": "integer"},
            "latest_post_date": {"type": "string"}
        },
        "required": ["signals", "open_roles", "tech_stack", "whitespace_summary", "confidence_score"]
    }

    for key, url in found_urls.items():
        if not url: continue
        print(f"\n--- SCRAPING {key.upper()}: {url} ---")
        scrape_payload = {
            "url": url,
            "formats": ["json"],
            "jsonOptions": {
                "prompt": "Extract strategic intelligence signals (expansion, new tech), recent updates, and hiring trends. Identify the most recent post date.",
                "schema": schema
            },
            "onlyMainContent": True
        }
        resp = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=scrape_payload, timeout=60)
        if resp.status_code == 200:
            print(json.dumps(resp.json().get("data", {}).get("json", {}), indent=2))
        else:
            print(f"Scrape failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    debug_full_pipe("codezilla.io")

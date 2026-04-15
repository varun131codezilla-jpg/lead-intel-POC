
import requests
import os
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

def debug_map(domain):
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    map_payload = {
        "url": f"https://{domain}",
        "search": "blog insights news careers jobs hiring"
    }
    
    print(f"Mapping domain: {domain}")
    resp = requests.post("https://api.firecrawl.dev/v1/map", headers=headers, json=map_payload, timeout=30)
    if resp.status_code == 200:
        links = resp.json().get("links", [])
        print(f"Found {len(links)} links")
        
        found_urls = {"blog": None, "career": None}
        for item in links:
            url = item.get("url", "").rstrip('/')
            url_lower = url.lower()
            
            # Blog detection
            if any(kw in url_lower for kw in ["blog", "insights", "news"]):
                if not found_urls["blog"] or len(url) < len(found_urls["blog"]):
                    found_urls["blog"] = url
                    print(f"NEW BLOG MATCH: {url}")
            
            # Career detection
            if any(kw in url_lower for kw in ["career", "jobs", "hiring"]):
                if not found_urls["career"] or len(url) < len(found_urls["career"]):
                    found_urls["career"] = url
                    print(f"NEW CAREER MATCH: {url}")
                    
        print(f"FINAL CHOICE: {found_urls}")
    else:
        print(f"MAP FAILED: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    debug_map("codezilla.io")

import requests
import os
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

def check_map():
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    map_payload = {"url": "https://codezilla.io"}
    resp = requests.post("https://api.firecrawl.dev/v1/map", headers=headers, json=map_payload, timeout=60)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        links = resp.json().get("links", [])
        print(f"Total links: {len(links)}")
        if links:
            print(f"First link type: {type(links[0])}")
            print(f"First link: {links[0]}")

if __name__ == "__main__":
    check_map()

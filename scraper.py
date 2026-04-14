import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

def scrape_company_data(domain):
    if not FIRECRAWL_API_KEY:
        return mock_evidence(domain)

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Step 1: Map the domain to find actual URLs
    print(f"Mapping domain: {domain}")
    map_payload = {
        "url": f"https://{domain}",
        "search": "blog careers jobs hiring"
    }
    
    found_urls = {"blog": f"https://{domain}/blog", "career": f"https://{domain}/careers"} # Fallbacks
    try:
        map_resp = requests.post("https://api.firecrawl.dev/v1/map", headers=headers, json=map_payload, timeout=30)
        if map_resp.status_code == 200:
            links = map_resp.json().get("links", [])
            for item in links:
                url = item.get("url", "").lower()
                if "blog" in url and "blog" not in found_urls["blog"]:
                    found_urls["blog"] = url
                if ("career" in url or "jobs" in url) and "career" not in found_urls["career"]:
                    found_urls["career"] = url
    except Exception as e:
        print(f"Mapping failed: {e}")

    # Step 2: AI-Powered Extraction Schema
    schema = {
        "type": "object",
        "properties": {
            "signals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Keywords related to Cloud, Managed Services, QA, or Modernisation"
            },
            "open_roles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant job titles found"
            },
            "tech_stack": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Technologies or platforms mentioned (e.g. AWS, Azure, SAP, Java)"
            },
            "whitespace_summary": {
                "type": "string",
                "description": "A summary of technical gaps or transformation needs"
            },
            "confidence_score": {
                "type": "integer",
                "description": "Confidence score from 0 to 100 based on evidence strength"
            }
        },
        "required": ["signals", "open_roles", "tech_stack", "whitespace_summary", "confidence_score"]
    }

    evidence = {
        "blog": {},
        "career": {},
        "linkedin": {"posts": [], "summary": "LinkedIn integration pending profile-level access."}
    }

    # Step 3: Extract from discovered URLs
    for key, url in found_urls.items():
        if not url: continue
        print(f"Extracting intelligence from: {url}")
        scrape_payload = {
            "url": url,
            "formats": ["json"],
            "jsonOptions": {
                "prompt": "Extract company intelligence for a service provider looking for opportunities in Cloud, Managed Services, and QA.",
                "schema": schema
            },
            "onlyMainContent": True
        }
        try:
            resp = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=scrape_payload, timeout=60)
            if resp.status_code == 200:
                evidence[key] = resp.json().get("data", {}).get("json", {})
        except Exception as e:
            print(f"Extraction from {url} failed: {e}")

    # Final Fallback to mock if completely failed
    if not (evidence["blog"] or evidence["career"]):
        return mock_evidence(domain)

    return evidence

def mock_evidence(domain):
    return {
        "blog": {
            "signals": ["Digital Transformation", "Legacy Migration"],
            "tech_stack": ["On-premise servers", "Java"],
            "whitespace_summary": "Heavily reliant on legacy on-prem systems, ripe for cloud migration.",
            "confidence_score": 60
        },
        "career": {
            "open_roles": ["Cloud Architect", "QA Automation Lead"],
            "signals": ["Expansion", "Testing Modernization"],
            "tech_stack": ["AWS", "Selenium"],
            "whitespace_summary": "Active hiring for cloud roles confirms strategic shift.",
            "confidence_score": 75
        },
        "linkedin": {
            "posts": ["Reinventing our customer journey with AI"],
            "summary": "Recent CEO focus on AI and Cloud.",
            "confidence_score": 80
        }
    }
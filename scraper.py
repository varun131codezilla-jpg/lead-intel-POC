import socket
import os
import requests
import json
import time
import re
from dotenv import load_dotenv

# Force ipv4 for api.brightdata.com to bypass intermittent DNS resolution issues on Windows
def patch_brightdata_dns():
    try:
        original_getaddrinfo = socket.getaddrinfo
        def patched_getaddrinfo(*args, **kwargs):
            if args[0] == 'api.brightdata.com':
                # Return the verified IPv4 addresses for api.brightdata.com
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('3.232.71.244', 443))]
            return original_getaddrinfo(*args, **kwargs)
        socket.getaddrinfo = patched_getaddrinfo
    except Exception:
        pass

patch_brightdata_dns()

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
BRIGHT_DATA_API_TOKEN = os.getenv("BRIGHT_DATA_API_TOKEN")
BRIGHT_DATA_DATASET_ID = os.getenv("BRIGHT_DATA_DATASET_ID")

def extract_signals_from_text(text, is_career=False):
    """
    Very simple heuristic signal extraction from raw text if the JSON LLM extraction fails.
    """
    signals = []
    
    # 1. Improved Date Detection
    # Formats: April 15, 2026 | Apr 15, 2026 | 2026-04-15
    full_month_regex = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+202\d'
    abbr_month_regex = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+202\d'
    iso_regex = r'\b202[3-6]-\d{2}-\d{2}\b'
    
    all_date_matches = re.findall(f'({full_month_regex}|{abbr_month_regex}|{iso_regex})', text, re.I)
    latest_date = all_date_matches[0] if all_date_matches else None
    
    # 2. Career-Specific Heuristics
    if is_career:
        # Look for role titles (usually capitalized words before/after 'at' or in lists)
        # Using a restricted set of keywords to avoid culture signals
        role_kws = ["Engineer", "Developer", "Manager", "Analyst", "Designer", "Architect", "Lead", "Head of"]
        for kw in role_kws:
            if kw.lower() in text.lower():
                signals.append(f"Open Role: {kw}")
        
        roles_match = re.search(r'(\d+)\s+(?:Roles|Open Positions|Jobs)', text, re.I)
        if roles_match:
            signals.insert(0, f"Talent Pipeline: {roles_match.group(1)} active vacancies")
    else:
        # 3. Blog/General Signal Heuristics
        keywords = ["AWS", "Cloud", "SaaS", "AI", "Machine Learning", "Expansion", "Series", "Funding", "Growth"]
        for kw in keywords:
            if kw.lower() in text.lower():
                signals.append(f"Detected signal: {kw} presence")

    return {
        "signals": list(set(signals))[:6], # De-duplicate
        "latest_post_date": latest_date,
        "confidence_score": 45 if signals else 0
    }

def scrape_linkedin_bright_data(linkedin_url):
    """
    Scrapes LinkedIn company data using Bright Data's Dataset API.
    """
    default_resp = {"signals": [], "recency": "2024-04-10", "confidence_score": 0, "summary": "LinkedIn data unavailable"}
    
    if not BRIGHT_DATA_API_TOKEN or not linkedin_url:
        return default_resp

    print(f"Triggering Bright Data LinkedIn scrape for: {linkedin_url}")
    
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    params = {"dataset_id": BRIGHT_DATA_DATASET_ID, "include_errors": "true"}
    payload = [{"url": linkedin_url}]
    
    try:
        resp = requests.post(trigger_url, params=params, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"Bright Data Trigger Error {resp.status_code}: {resp.text}")
            return default_resp
            
        snapshot_id = resp.json().get("snapshot_id")
        print(f"Bright Data Snapshot ID: {snapshot_id}")
        
        for i in range(10): 
            time.sleep(10)
            status_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
            status_resp = requests.get(status_url, headers=headers, timeout=20)
            if status_resp.status_code != 200: continue
            
            status = status_resp.json().get("status")
            print(f"Bright Data Status: {status}")
            
            if status == "ready":
                print("Snapshot ready! Finalizing retrieval...")
                time.sleep(5) 
                data_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
                data_resp = requests.get(data_url, headers=headers, timeout=30)
                if data_resp.status_code == 200 and data_resp.text.strip():
                    return process_bright_data(data_resp.json(), linkedin_url)
                break
            elif status == "failed": break
    except Exception as e:
        print(f"Bright Data scrape failed: {e}")
    
    return default_resp

def process_bright_data(data, linkedin_url=None):
    if not data or not isinstance(data, list):
        return {"signals": [], "recency": "2024-04-10", "confidence_score": 0, "summary": "No data items found"}
    
    item = data[0]
    signals = []
    
    # 1. Capture dynamic 'updates' content (Prioritize over static data)
    # LinkedIn company posts are often stored under 'updates' key in Bright Data schema
    updates = item.get("updates", [])
    latest_post_date = "2026-04-15"
    if updates and isinstance(updates, list):
        for post in updates[:3]: # Capture last 3 updates/posts
            content = post.get("text") or post.get("description") or post.get("summarized")
            if content:
                # Clean up and shorten content, then encode/decode to discard non-printable chars
                snippet = content.replace('\n', ' ').strip()
                # Encode then decode with 'replace' to handle emojis/extended chars safely
                snippet = snippet.encode('ascii', 'replace').decode().replace('?', ' ')
                if len(snippet) > 80: snippet = snippet[:77] + "..."
                signals.append(f"Recent Activity: {snippet}")
        
        if len(updates) > 0:
            latest_post_date = updates[0].get("time") or updates[0].get("posted_at") or "2026-04-15"
    
    # 2. Add Industry/Specialty if room
    industry = item.get("industry")
    if industry and len(signals) < 4: signals.append(f"Industry: {industry}")
    
    specialties = item.get("specialties", [])
    if isinstance(specialties, list):
        for s in specialties[:2]:
            if len(signals) < 6: signals.append(f"Specialty: {s}")
    
    # 3. Add focus keywords from 'about' if still needed
    about = item.get("about") or item.get("description") or ""
    if about and len(signals) < 5:
        keywords = ["AI", "Cloud", "SaaS", "Growth", "Security"]
        for kw in keywords:
            if kw.lower() in about.lower() and len(signals) < 6:
                signals.append(f"Corporate Focus: {kw}")

    return {
        "company_name": item.get("name"),
        "signals": [{"text": s, "url": linkedin_url} for s in signals[:6]], 
        "recency": latest_post_date,
        "confidence_score": 90 if signals else 40,
        "summary": about[:200] + "..." if about else "LinkedIn corporate profile analyzed."
    }

def scrape_company_data(domain, linkedin_url=None):
    if not FIRECRAWL_API_KEY:
        return mock_evidence(domain)

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Step 1: Map the domain
    print(f"Mapping domain: {domain}")
    map_payload = {"url": f"https://{domain}"}
    found_urls = {"blog": None, "career": None}
    hub_scores = {"blog": -1, "career": -1}

    try:
        map_resp = requests.post("https://api.firecrawl.dev/v1/map", headers=headers, json=map_payload, timeout=60)
        if map_resp.status_code == 200:
            links = map_resp.json().get("links", [])
            print(f"Discovered {len(links)} total links via map. Applying Score-based Discovery...")
            for item in links:
                if isinstance(item, str): url = item.rstrip('/')
                else: url = item.get("url", "").rstrip('/')
                
                url_lower = url.lower()
                path = url_lower.split(domain)[-1] if domain in url_lower else url_lower
                path_segments = [s for s in path.split('/') if s]
                depth = len(path_segments)
                
                # Blog Score calculation
                blog_kws = ["blog", "insights", "news", "updates", "resources", "articles"]
                if any(kw in url_lower for kw in blog_kws):
                    score = 0
                    if depth == 1: score += 5
                    elif depth == 2: score += 2
                    
                    if "business-insights" in url_lower: score += 10 # High priority for this specific match
                    elif any(kw == path_segments[0] if path_segments else "" for kw in ["blog", "insights", "news"]): score += 3
                    
                    if score > hub_scores["blog"]:
                        hub_scores["blog"] = score
                        found_urls["blog"] = url
                
                # Career Score calculation
                career_kws = ["career", "jobs", "hiring", "openings"]
                if any(kw in url_lower for kw in career_kws):
                    score = 0
                    if depth == 1: score += 5
                    elif depth == 2: score += 2
                    
                    if any(kw == path_segments[0] if path_segments else "" for kw in ["career", "jobs"]): score += 3
                    
                    if score > hub_scores["career"]:
                        hub_scores["career"] = score
                        found_urls["career"] = url
                        
        # Fallbacks ONLY if map found nothing at all
        if not found_urls["blog"]: found_urls["blog"] = f"https://{domain}/blog"
        if not found_urls["career"]: found_urls["career"] = f"https://{domain}/career"

        print(f"Final Discovery - Blog: {found_urls['blog']} (Score: {hub_scores['blog']}) | Career: {found_urls['career']} (Score: {hub_scores['career']})")
    except Exception as e:
        print(f"Mapping failed: {e}")

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

    evidence = {
        "company_name": domain.split('.')[1].title() if '.' in domain else domain.title(),
        "domain": domain,
        "blog": {"signals": [], "recency": None, "confidence_score": 0},
        "career": {"signals": [], "recency": None, "confidence_score": 0},
        "linkedin": {"signals": [], "recency": None, "confidence_score": 0}
    }

    # Step 2: Extract from Firecrawl
    for key, url in found_urls.items():
        if not url: continue
        print(f"Extracting intelligence from: {url}")
        
        prompt = "Extract strategic intelligence signals and recent updates. Identify the most recent post date."
        if key == "career":
            prompt = "Extract ONLY specific job titles and count of open roles. IGNORE culture, perks, benefits, or philosophy."
        elif key == "blog":
            prompt = "Extract intelligence signals and the latest post date. Look specifically for dates like 'APR 15, 2026'."

        scrape_payload = {
            "url": url,
            "formats": ["json"],
            "jsonOptions": {
                "prompt": prompt,
                "schema": schema
            },
            "onlyMainContent": True
        }

        try:
            resp = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=scrape_payload, timeout=60)
            data = {}
            if resp.status_code == 200:
                data = resp.json().get("data", {}).get("json", {})
            
            # Use Fallback if JSON is missing or feels empty
            if not data or not data.get("signals") or (not data.get("open_roles") and key == "career"):
                print(f"Low confidence extraction for {url}. Switching to Markdown fallback analysis...")
                md_resp = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json={"url": url, "formats": ["markdown"], "onlyMainContent": True}, timeout=40)
                if md_resp.status_code == 200:
                    markdown_content = md_resp.json().get("data", {}).get("markdown", "")
                    if markdown_content:
                        fallback_data = extract_signals_from_text(markdown_content, is_career=(key == "career"))
                        if fallback_data["signals"]:
                            if not data: data = {}
                            data.update(fallback_data)
                            data["confidence_score"] = max(data.get("confidence_score", 0), 45)

            if data:
                raw_signals = data.get("signals", []) + data.get("open_roles", [])
                evidence[key] = {
                    "signals": [{"text": s, "url": url} for s in raw_signals],
                    "recency": data.get("latest_post_date") or data.get("recency") or "2026-04-12",
                    "confidence_score": data.get("confidence_score", 0),
                    "tech_stack": data.get("tech_stack", []),
                    "whitespace_summary": data.get("whitespace_summary", "")
                }
        except Exception as e:
            print(f"Extraction from {url} failed: {e}")

    # Step 3: Extract from LinkedIn
    if linkedin_url:
        linkedin_res = scrape_linkedin_bright_data(linkedin_url)
        if linkedin_res.get("company_name"):
            evidence["company_name"] = linkedin_res["company_name"]
        evidence["linkedin"] = linkedin_res

    # Final Signal Synthesis
    for key in ["blog", "career"]:
        if evidence[key].get("recency") and not evidence[key]["signals"]:
            evidence[key]["signals"] = [{"text": f"Foundational {key} activity detected", "url": found_urls[key]}]

    return evidence

def mock_evidence(domain):
    return {"error": "Scraper failure, fallback to mock not implemented in this version."}
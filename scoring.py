import datetime

def calculate_recency_score(date_str):
    """
    Calculates a score from 0-100 based on how recent the date is.
    Now more robust: extracts the date part from noisy strings using regex.
    """
    if not date_str or not isinstance(date_str, str):
        return 0

    import re
    today = datetime.datetime.now()
    
    # 1. NEW: Try to extract a date pattern from the string first
    # Regexes for common formats
    patterns = [
        r'(\b\d{4}-\d{1,2}-\d{1,2}\b)', # YYYY-MM-DD
        r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b)', # Month DD, YYYY
        r'(\b\d{1,2}/\d{1,2}/\d{4}\b)', # MM/DD/YYYY or DD/MM/YYYY
        r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b)', # Month YYYY
    ]
    
    cleaned_date = date_str.strip()
    
    # Check for relative time FIRST (16h, 1w, etc.)
    relative_match = re.search(r"(\d+)\s*(h|d|w|mo|y|yr)", cleaned_date.lower())
    if relative_match:
        val = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit == 'h': return 100
        if unit == 'd': return 100 if val <= 7 else 90
        if unit == 'w': return 100 if val == 1 else 90
        if unit == 'mo': return 75 if val == 1 else 50
        if unit in ['y', 'yr']: return 20 if val == 1 else 10

    # Try to find a date match
    matched_str = None
    for pat in patterns:
        match = re.search(pat, cleaned_date, re.I)
        if match:
            matched_str = match.group(1)
            break
    
    if not matched_str:
        # If no regex match, fall back to title-cased cleaned string (previous behavior)
        matched_str = cleaned_date.title()
    else:
        matched_str = matched_str.title()

    formats = [
        "%Y-%m-%d",          # 2026-04-15
        "%b %d, %Y",         # Apr 15, 2026
        "%B %d, %Y",         # April 15, 2026
        "%m/%d/%Y",          # 04/15/2026 (assumes US but strptime handles simple)
        "%B %Y",             # April 2026
        "%Y"                 # 2026
    ]
    
    # Clean ISO markers
    if "T" in matched_str:
        matched_str = matched_str.split("T")[0]

    for fmt in formats:
        try:
            post_date = datetime.datetime.strptime(matched_str, fmt)
            diff = (today - post_date).days
            
            if diff <= 7: return 100
            if diff <= 14: return 90
            if diff <= 30: return 75
            if diff <= 90: return 50
            if diff <= 365: return 20
            return 10
        except ValueError:
            continue
            
    return 0


def calculate_account_360_score(evidence):
    # Weights for individual sources
    BLOG_WEIGHT = 0.30
    CAREER_WEIGHT = 0.40
    LINKED_WEIGHT = 0.30
    
    results = {
        "lead_name": evidence.get("lead_name", "Strategic Target"),
        "lead_linkedin": evidence.get("lead_linkedin", ""),
        "company_name": evidence.get("company_name", "Unknown Company"),
        "domain": evidence.get("domain", "website.com"),


        "blog": {"score": 0, "recency": 0, "signals": []},
        "career": {"score": 0, "recency": 0, "signals": []},
        "linkedin": {"score": 0, "recency": 0, "signals": []},
        "composite_score": 0,
        "confidence_band": "N/A",
        "details": {"whitespace_insight": ""}
    }

    # 1. Process Blog
    blog_data = evidence.get("blog", {})
    results["blog"]["signals"] = blog_data.get("signals", [])
    if not results["blog"]["signals"]:
        results["blog"]["recency"] = 0
        results["blog"]["score"] = 0
    else:
        results["blog"]["recency"] = calculate_recency_score(blog_data.get("recency"))
        # Blog Confidence = (Signals Quality * 0.6) + (Recency * 0.4)
        sig_quality = min(100, len(results["blog"]["signals"]) * 25)
        if results["blog"]["recency"] > 0:
            results["blog"]["score"] = round((sig_quality * 0.6) + (results["blog"]["recency"] * 0.4))
        else:
            # Fallback score if signals exist but no date found
            results["blog"]["score"] = round(sig_quality * 0.5)

    
    # 2. Process Career
    career_data = evidence.get("career", {})
    results["career"]["signals"] = career_data.get("signals", [])
    if not results["career"]["signals"]:
        results["career"]["recency"] = 0
        results["career"]["score"] = 0
    else:
        results["career"]["recency"] = calculate_recency_score(career_data.get("recency"))
        # Career Confidence 
        career_sig_quality = min(100, len(results["career"]["signals"]) * 30)
        if results["career"]["recency"] > 0:
            results["career"]["score"] = round((career_sig_quality * 0.6) + (results["career"]["recency"] * 0.4))
        else:
            # Baseline score for active portal/roles even if no date is listed
            results["career"]["score"] = round(career_sig_quality * 0.6)

    
    # 3. Process LinkedIn
    linkedin_data = evidence.get("linkedin", {})
    results["linkedin"]["signals"] = linkedin_data.get("signals", [])
    if not results["linkedin"]["signals"]:
        results["linkedin"]["recency"] = 0
        results["linkedin"]["score"] = 0
    else:
        results["linkedin"]["recency"] = calculate_recency_score(linkedin_data.get("recency"))
        # LinkedIn Confidence
        link_sig_quality = min(100, len(results["linkedin"]["signals"]) * 20 + 20)
        if results["linkedin"]["recency"] > 0:
            results["linkedin"]["score"] = round((link_sig_quality * 0.6) + (results["linkedin"]["recency"] * 0.4))
        else:
            # Fallback for LinkedIn activity found but timestamp missing/unparsed
            results["linkedin"]["score"] = round(link_sig_quality * 0.5)

    
    # 4. Composite Score
    composite = (results["blog"]["score"] * BLOG_WEIGHT) + \
                (results["career"]["score"] * CAREER_WEIGHT) + \
                (results["linkedin"]["score"] * LINKED_WEIGHT)
    
    results["composite_score"] = round(composite, 1)
    
    # Confidence Band
    if composite >= 85: results["confidence_band"] = "High Propensity"
    elif composite >= 60: results["confidence_band"] = "Developing Intent"
    elif composite > 0: results["confidence_band"] = "Minimal Signal"
    else: results["confidence_band"] = "No Signals Detected"
    
    # Insights
    results["details"]["whitespace_insight"] = (blog_data.get("whitespace_summary") or career_data.get("whitespace_summary") or "Consolidated signals suggest high-intent engagement.")
    
    return results

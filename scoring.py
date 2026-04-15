import datetime

def calculate_recency_score(date_str):
    """
    Calculates a score from 0-100 based on how recent the date is.
    Assumes date_str is in YYYY-MM-DD or similar format.
    """
    if not date_str or not isinstance(date_str, str):
        return 50 # Default middle
    
    try:
        # Simple heuristic: older than 30 days = lower score
        # Use dynamic 'now' to ensure recency scoring is accurate regardless of current year.
        today = datetime.datetime.now()

        post_date = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d")
        diff = (today - post_date).days
        
        if diff <= 7: return 100
        if diff <= 14: return 90
        if diff <= 30: return 75
        if diff <= 90: return 50
        return 20
    except:
        return 60

def calculate_account_360_score(evidence):
    # Weights for individual sources
    BLOG_WEIGHT = 0.30
    CAREER_WEIGHT = 0.40
    LINKED_WEIGHT = 0.30
    
    results = {
        "lead_name": evidence.get("lead_name", "Strategic Target"),
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
    results["blog"]["recency"] = calculate_recency_score(blog_data.get("recency"))
    # Blog Confidence = (Signals Quality * 0.6) + (Recency * 0.4)
    sig_quality = min(100, len(results["blog"]["signals"]) * 25)
    results["blog"]["score"] = round((sig_quality * 0.6) + (results["blog"]["recency"] * 0.4))
    
    # 2. Process Career
    career_data = evidence.get("career", {})
    results["career"]["signals"] = career_data.get("signals", [])
    results["career"]["recency"] = calculate_recency_score(career_data.get("recency"))
    # Career Confidence 
    career_sig_quality = min(100, len(results["career"]["signals"]) * 30)
    results["career"]["score"] = round((career_sig_quality * 0.6) + (results["career"]["recency"] * 0.4))
    
    # 3. Process LinkedIn
    linkedin_data = evidence.get("linkedin", {})
    results["linkedin"]["signals"] = linkedin_data.get("signals", [])
    results["linkedin"]["recency"] = calculate_recency_score(linkedin_data.get("recency"))
    # LinkedIn Confidence
    link_sig_quality = min(100, len(results["linkedin"]["signals"]) * 20 + 20)
    results["linkedin"]["score"] = round((link_sig_quality * 0.6) + (results["linkedin"]["recency"] * 0.4))
    
    # 4. Composite Score
    composite = (results["blog"]["score"] * BLOG_WEIGHT) + \
                (results["career"]["score"] * CAREER_WEIGHT) + \
                (results["linkedin"]["score"] * LINKED_WEIGHT)
    
    results["composite_score"] = round(composite, 1)
    
    # Score bands
    if composite >= 85: band = "High Propensity"
    elif composite >= 60: band = "Strategic Fit"
    elif composite >= 40: band = "Moderate"
    else: band = "Developing"
    results["confidence_band"] = band
    
    # Insights
    results["details"]["whitespace_insight"] = (blog_data.get("whitespace_summary") or career_data.get("whitespace_summary") or "Consolidated signals suggest high-intent engagement.")
    
    return results

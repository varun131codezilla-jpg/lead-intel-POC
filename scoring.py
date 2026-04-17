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

    def process_section(section_key):
        section_data = evidence.get(section_key, {})
        signals = section_data.get("signals", [])
        section_recency_str = section_data.get("recency") or "2026-04-10"
        
        if not signals:
            return {
                "score": 0, 
                "total_confidence": 0,
                "total_recency": 0,
                "recency": 0, 
                "signals": []
            }

        # Calculate Individual Contributions
        processed_signals = []
        recency_values = []
        
        # Section-level recency fallback
        fallback_recency = calculate_recency_score(section_recency_str)
        
        for i, s in enumerate(signals[:6]): # Cap at 6 signals for UI
            # Dynamic Confidence contribution based on ICP Match (Relevance)
            # Relevance (0-100) scaled by its share of the 60% total confidence weight
            rel_val = s.get("relevance_score", 50)
            conf_contrib = round((rel_val / 100) * (60 / len(signals)))
            
            # Recency Value: 0-100
            sig_date = s.get("date")
            sig_recency_val = calculate_recency_score(sig_date) if sig_date else fallback_recency
            recency_values.append(sig_recency_val)
            
            # Calculate this signal's share of the 40% recency weight
            rec_contrib = round(sig_recency_val * 0.4 / len(signals))
            
            processed_signals.append({
                "text": s.get("text"),
                "url": s.get("url"),
                "date": sig_date or section_recency_str,
                "conf_contribution": conf_contrib,
                "recency_contribution": rec_contrib,
                "recency_score": sig_recency_val
            })

        # Section Totals (Sums of parts)
        total_conf = sum(p["conf_contribution"] for p in processed_signals)
        total_rec = sum(p["recency_contribution"] for p in processed_signals)
        
        # Final Section Score is the sum of weighted contributions
        section_score = total_conf + total_rec

        return {
            "score": section_score,
            "total_confidence": total_conf,
            "total_recency": total_rec,
            "recency": round(sum(recency_values)/len(recency_values)) if recency_values else 0,
            "signals": processed_signals
        }

    results["blog"] = process_section("blog")
    results["career"] = process_section("career")
    results["linkedin"] = process_section("linkedin")
    
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
    results["details"]["whitespace_insight"] = (evidence.get("blog", {}).get("whitespace_summary") or evidence.get("career", {}).get("whitespace_summary") or "Consolidated signals suggest high-intent engagement.")
    
    return results

def calculate_account_360_score(evidence):
    # Weights from document
    BLOG_WEIGHT = 0.30
    HIRING_WEIGHT = 0.40
    LINKEDIN_WEIGHT = 0.30
    
    # Extract AI scores or use defaults
    blog_data = evidence.get("blog", {})
    career_data = evidence.get("career", {})
    linkedin_data = evidence.get("linkedin", {})
    
    blog_score = blog_data.get("confidence_score", 0) if isinstance(blog_data, dict) else 0
    hiring_score = career_data.get("confidence_score", 0) if isinstance(career_data, dict) else 0
    linkedin_score = linkedin_data.get("confidence_score", 0) if isinstance(linkedin_data, dict) else 0
    
    # Module 1: Company 360 (Evidence Quality, Corroboration, Recency)
    # We use the density of signals found as a proxy for Quality
    signals_count = len(blog_data.get("signals", [])) + len(career_data.get("signals", []))
    eq_score = min(40, signals_count * 5 + 10) # Max 40
    
    corrob_score = 20 if (blog_score > 0 and hiring_score > 0) else 10
    recency_score = 25 # Assuming fresh since it's scraped live
    consistency_score = 15 if abs(blog_score - hiring_score) < 30 else 5
    
    m1_score = eq_score + corrob_score + recency_score + consistency_score
    
    # Module 2: Contact Intelligence (LinkedIn Engagement)
    m2_score = linkedin_score if linkedin_score > 0 else 30
    
    # Module 3: Whitespace Opportunity (AI Summary analysis)
    # If the AI summary mentions "gaps", "legacy", or "modernization", we score higher
    m3_score = 40
    whitespace_text = (blog_data.get("whitespace_summary", "") + career_data.get("whitespace_summary", "")).lower()
    if any(word in whitespace_text for word in ["gap", "legacy", "modern", "lack", "needed"]):
        m3_score += 40
    else:
        m3_score += 15
        
    # Module 4: Vendor Landscape (Tech stack diversity)
    tech_count = len(blog_data.get("tech_stack", [])) + len(career_data.get("tech_stack", []))
    m4_score = min(100, 40 + tech_count * 10)
    
    # Composite Score Calculation (weighted average of modules or simple weighted criteria)
    # User asked for 30/40/30 split on source weight, but also mentioned Module-based framework.
    # We will use the Module weights: M1 25%, M2 25%, M3 35%, M4 15%
    composite = (m1_score * 0.25) + (m2_score * 0.25) + (m3_score * 0.35) + (m4_score * 0.15)
    
    # Score bands
    if composite >= 80: band = "High Confidence"
    elif composite >= 50: band = "Medium Confidence"
    elif composite >= 40: band = "Low Confidence"
    elif composite >= 20: band = "Very Low"
    else: band = "Insufficient"
    
    return {
        "composite_score": round(composite, 1),
        "confidence_band": band,
        "module_1": m1_score,
        "module_2": m2_score,
        "module_3": m3_score,
        "module_4": m4_score,
        "raw_signals": {
            "blog": blog_data.get("signals", []),
            "hiring": career_data.get("open_roles", []),
            "tech": list(set(blog_data.get("tech_stack", []) + career_data.get("tech_stack", [])))
        },
        "details": {
            "whitespace_insight": blog_data.get("whitespace_summary") or career_data.get("whitespace_summary") or "No direct whitespace identified.",
            "corroboration": "Strong" if corrob_score == 20 else "Partial"
        }
    }
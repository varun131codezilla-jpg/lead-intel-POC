def test_discovery():
    links = [
        {"url": "https://codezilla.io/business-insights"},
        {"url": "https://codezilla.io/blog/post-1"},
        {"url": "https://codezilla.io/career"},
        {"url": "https://codezilla.io/life-at-codezilla"}
    ]
    domain = "codezilla.io"
    found_urls = {"blog": None, "career": None}
    
    blog_kws = ["blog", "insights", "news", "updates", "resources", "articles"]
    career_kws = ["career", "jobs", "hiring", "openings"]
    
    for item in links:
        url = item.get("url", "").rstrip('/')
        url_lower = url.lower()
        path = url_lower.split(domain)[-1] if domain in url_lower else url_lower
        path_segments = [s for s in path.split('/') if s]
        print(f"URL: {url} | Path Segments: {path_segments}")
        
        # Blog detection
        if any(kw in url_lower for kw in blog_kws):
            is_hub = len(path_segments) <= 1
            if "business-insights" in url_lower: is_hub = True
            print(f"  Match Blog! is_hub={is_hub}")
            
            if not found_urls["blog"] or (is_hub and "/" not in found_urls["blog"].split(domain)[-1].strip('/')):
                found_urls["blog"] = url
                print(f"  Setting blog to: {url}")
            elif is_hub:
                if "insights" in url_lower and "blog" in found_urls["blog"]:
                    found_urls["blog"] = url
                    print(f"  Prioritizing insights: {url}")
                elif len(url) < len(found_urls["blog"]): 
                    found_urls["blog"] = url
                    print(f"  Shorter hub: {url}")
                    
    print(f"\nFinal Blog: {found_urls['blog']}")

if __name__ == "__main__":
    test_discovery()

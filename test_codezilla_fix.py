from scraper import scrape_company_data
from scoring import calculate_account_360_score
import json

def test_fix():
    domain = "codezilla.io"
    linkedin_url = "https://www.linkedin.com/company/codezillians/"
    
    print(f"Testing fix for {domain}...")
    evidence = scrape_company_data(domain, linkedin_url=linkedin_url)
    
    print("\nEvidence Found:")
    print(f"Blog URL: {evidence.get('blog_url', 'N/A')} (Check if it's business-insights)")
    # Note: scrape_company_data doesn't return the URL in the dictionary easily, but we can check signals
    
    print("\nSignals:")
    print("Blog Signals:", len(evidence['blog']['signals']))
    print("Career Signals:", len(evidence['career']['signals']))
    print("LinkedIn Signals:", len(evidence['linkedin']['signals']))
    for sig in evidence['linkedin']['signals']:
        print(f"  - {sig['text']}")
    
    scores = calculate_account_360_score(evidence)
    print("\nScores:")
    print(f"Blog Score: {scores['blog']['score']} (Recency: {scores['blog']['recency']})")
    print(f"Career Score: {scores['career']['score']} (Recency: {scores['career']['recency']})")
    print(f"Composite Score: {scores['composite_score']}")

if __name__ == "__main__":
    test_fix()

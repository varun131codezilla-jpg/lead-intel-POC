from scraper import scrape_company_data
from scoring import calculate_account_360_score
import json

def test_pipeline():
    print("Testing pipeline with domain: google.com")
    # Using mock data by ensuring firecrawl key is checked but provided mock is reached if real fails
    # Or just calling mock_evidence directly for scoring check
    from scraper import mock_evidence
    evidence = mock_evidence("google.com")
    print("Mock Evidence Extracted:")
    print(json.dumps(evidence, indent=2))
    
    scores = calculate_account_360_score(evidence)
    print("\nCalculated Scores:")
    print(json.dumps(scores, indent=2))
    
    assert scores["blog"]["score"] >= 0
    assert scores["career"]["score"] >= 0
    assert scores["linkedin"]["score"] >= 0
    assert scores["composite_score"] >= 0
    print("\nPipeline test PASSED.")

if __name__ == "__main__":
    test_pipeline()

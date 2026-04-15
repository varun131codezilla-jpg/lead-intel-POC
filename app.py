import os
from flask import Flask, render_template, request, jsonify
from scraper import scrape_company_data
from scoring import calculate_account_360_score
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/terminal')
def terminal():
    return render_template('terminal.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    website = data.get('website')
    linkedin_url = data.get('linkedin_url')
    lead_name = data.get('lead_name', 'Strategic Target')

    
    if not website:
        return jsonify({"error": "No website provided"}), 400

    # Extract domain from website URL if needed
    domain = website.replace('https://', '').replace('http://', '').split('/')[0]

    print(f"Scraping evidence for {domain} with LinkedIn: {linkedin_url}...")
    try:
        evidence = scrape_company_data(domain, linkedin_url=linkedin_url)
        evidence["lead_name"] = lead_name
        print(f"Analyzing {lead_name} at {domain}...")
        scores = calculate_account_360_score(evidence)

    except Exception as e:
        print(f"Analysis failed: {e}")
        # Final fallback if even the scraper fallback fails
        from scraper import mock_evidence
        evidence = mock_evidence(domain)
        scores = calculate_account_360_score(evidence)
    
    return jsonify({
        "domain": domain,
        "evidence": evidence,
        "scores": scores
    })



if __name__ == '__main__':
    app.run(debug=True, port=5000)
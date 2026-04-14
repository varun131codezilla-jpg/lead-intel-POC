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

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    domain = data.get('domain')
    
    if not domain:
        return jsonify({"error": "No domain provided"}), 400

    print(f"Scraping evidence for {domain}...")
    evidence = scrape_company_data(domain)
    
    print("Calculating scores...")
    scores = calculate_account_360_score(evidence)
    
    return jsonify({
        "domain": domain,
        "evidence": evidence,
        "scores": scores
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
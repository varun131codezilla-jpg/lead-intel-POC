# AI Lead Intelligence Engine 🧠⚡

A high-fidelity Proof of Concept for an **AI-powered lead qualification pipeline**. This engine uses Firecrawl's AI extraction and mapping to turn company websites, blogs, and career pages into actionable market intelligence.

## 🚀 Overview
The Lead Intelligence Engine moves beyond basic keyword matching. It uses semantic understanding to identify high-propensity signals for managed services, cloud infrastructure, and software modernization.

### Key Features
- **Smart Discovery**: Automatically maps target domains to find relevant Career and Blog subpages.
- **AI Synthesis**: Extract structured JSON data (tech stack, service line matches, strategic gaps) using Firecrawl's LLM engine.
- **Account 360 Scoring**: A weighted scoring algorithm (30% Blog, 40% Careers, 30% Social) aligned with the "Editorial Intelligence" framework.
- **Premium UI**: Dark-mode strategist dashboard inspired by high-end intelligence terminals.

## 🛠️ Setup & Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd POC-lead
   ```

2. **Install dependencies**
   ```bash
   pip install flask python-dotenv requests
   ```

3. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```
   Navigate to `http://127.0.0.1:5000` to start analyzing leads.

## 📊 Scoring Methodology
The engine calculates a **Confidence Score** based on four intelligence modules:
- **Service Line Fit** (Cloud, Managed Services, QA, Modernization)
- **Hiring Velocity** (Job titles and expansion signals)
- **Content Strategy** (Company blog analysis)
- **Social Pulse** (Engagement signals)

## 📜 License
Internal POC - Proprietary

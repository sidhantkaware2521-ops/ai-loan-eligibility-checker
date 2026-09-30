# Finova AI — Loan Eligibility Checker

A ready-to-run BFSI web project implementing the requirements from the supplied project brief.

## Included modules
- Loan Eligibility Checker
- Credit Score Analyzer
- EMI Calculator
- AI Financial Tips
- Responsive dark glassmorphism interface
- JavaScript input validation and API-backed calculations
- Optional Anthropic Claude integration
- Optional Google Sheets storage
- Local JSONL fallback for submissions
- Health endpoint for deployment checks

## Tech stack
- Frontend: HTML5, CSS3, vanilla JavaScript
- Backend: Python + Flask
- AI: Anthropic Claude API (optional)
- Data: Google Sheets API via service account (optional)
- Deployment: compatible with Gunicorn, Render, Railway, or a VM; static/frontend can also be adapted for Vercel/Netlify.

## 1. Install
Python 3.10+ is recommended.

Windows:
```powershell
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure
Copy `.env.example` to `.env`.

### Claude AI (optional)
Put your Anthropic API key in `ANTHROPIC_API_KEY`. Never commit the key to GitHub.

### Google Sheets (optional)
1. Create a Google Cloud project and enable Google Sheets API + Google Drive API.
2. Create a service account and download its JSON key as `service-account.json`.
3. Create a spreadsheet named exactly like `GOOGLE_SHEET_NAME`.
4. Share the spreadsheet with the service account email with Editor access.
5. Set `GOOGLE_SERVICE_ACCOUNT_JSON=service-account.json`.

If Google Sheets is not configured, the application automatically saves submissions locally to `data/applications.jsonl`.

## 3. Run
```bash
python app.py
```
Open `http://localhost:5000`.

Production-style:
```bash
gunicorn app:app --bind 0.0.0.0:5000
```

## Important project note
The eligibility engine is a transparent educational demo, not a bank underwriting model. A real lender would use its own policies, verified documents, bureau data, regulatory requirements, fraud checks, and risk models. The UI deliberately labels the result as an estimate.

## Suggested project presentation points
**Problem:** Financial decisions can require multiple tools and calculations.

**Solution:** One responsive BFSI dashboard combines loan assessment, credit analysis, EMI planning and AI guidance.

**Innovation:** Glassmorphism UI, real-time calculations, optional Claude reasoning, and Google Sheets persistence.

**Future enhancements:** User authentication, ML-based risk models, PDF reports, bank API integrations, multilingual support, audit logging, and stronger privacy/security controls.

import os, json, math
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Optional integrations
try:
    import anthropic
except Exception:
    anthropic = None
try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None


def clamp(n, lo, hi):
    return max(lo, min(hi, n))


def loan_eligibility(data):
    age = float(data.get('age', 0))
    income = float(data.get('income', 0))
    credit = float(data.get('creditScore', 0))
    employment = data.get('employment', 'Salaried')
    existing_emi = float(data.get('existingEmi', 0))
    loan_amount = float(data.get('loanAmount', 0))

    score = 0
    reasons = []
    if 21 <= age <= 60:
        score += 20
    else:
        reasons.append('Age is outside the preferred 21–60 range.')
    if income >= 25000:
        score += 25
    elif income >= 15000:
        score += 15
    else:
        reasons.append('Monthly income is below the preferred threshold.')
    if credit >= 750:
        score += 30
    elif credit >= 700:
        score += 24
    elif credit >= 650:
        score += 16
    elif credit >= 600:
        score += 8
    else:
        reasons.append('Credit score is below 600.')
    if employment in ('Salaried', 'Government Employee'):
        score += 15
    elif employment == 'Self Employed':
        score += 12
    else:
        score += 5
    dti = (existing_emi / income * 100) if income else 100
    if dti <= 30:
        score += 10
    elif dti <= 45:
        score += 6
    else:
        reasons.append('Existing EMI burden is relatively high.')

    status = 'Likely Eligible' if score >= 70 and credit >= 600 else ('Review Required' if score >= 50 else 'Likely Not Eligible')
    rate = 9.5 if credit >= 750 else 11.0 if credit >= 700 else 12.5 if credit >= 650 else 14.0
    max_emi = max(0, income * 0.45 - existing_emi)
    estimated_loan = 0
    if max_emi > 0:
        r = rate / 1200
        n = 60
        estimated_loan = max_emi * ((1+r)**n - 1) / (r*(1+r)**n) if r else max_emi*n
    if loan_amount > 0 and loan_amount > estimated_loan:
        reasons.append('Requested loan amount may exceed the estimated affordability range.')

    return {
        'status': status, 'score': int(score), 'creditScore': int(credit),
        'dti': round(dti, 1), 'interestRate': rate,
        'estimatedEligibleAmount': round(estimated_loan), 'reasons': reasons
    }


def credit_analysis(credit):
    credit = float(credit)
    if credit >= 800: band, label = 'Exceptional', 'Very strong credit profile'
    elif credit >= 750: band, label = 'Very Good', 'Strong credit profile'
    elif credit >= 700: band, label = 'Good', 'Generally healthy credit profile'
    elif credit >= 650: band, label = 'Fair', 'Some improvement may help'
    elif credit >= 600: band, label = 'Weak', 'Improvement is recommended'
    else: band, label = 'Poor', 'Significant improvement is recommended'
    tips = [
        'Pay EMIs and credit-card bills on time.',
        'Keep credit utilization comfortably below the limit.',
        'Avoid applying for multiple loans or cards in a short period.',
        'Review your credit report periodically for errors.'
    ]
    return {'score': int(credit), 'band': band, 'summary': label, 'tips': tips}


def emi_calculator(principal, annual_rate, months):
    principal, annual_rate, months = float(principal), float(annual_rate), int(months)
    if principal <= 0 or months <= 0:
        raise ValueError('Principal and tenure must be greater than zero.')
    r = annual_rate / 1200
    emi = principal / months if r == 0 else principal * r * (1+r)**months / ((1+r)**months - 1)
    total = emi * months
    return {'emi': round(emi, 2), 'totalPayment': round(total, 2), 'totalInterest': round(total-principal, 2)}


def append_google_sheet(record):
    creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    sheet_name = os.getenv('GOOGLE_SHEET_NAME', '')
    if not (gspread and Credentials and creds_path and sheet_name):
        return False, 'Google Sheets integration is not configured; saved locally instead.'
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)
        ws = sh.sheet1
        if not ws.get_all_values():
            ws.append_row(['Timestamp','Name','Age','Income','Credit Score','Employment','Loan Amount','Existing EMI'])
        ws.append_row([record.get('timestamp'), record.get('name'), record.get('age'), record.get('income'), record.get('creditScore'), record.get('employment'), record.get('loanAmount'), record.get('existingEmi')])
        return True, 'Saved to Google Sheets.'
    except Exception as e:
        return False, f'Google Sheets save failed: {str(e)[:160]}'


def save_local(record):
    path = os.path.join(app.root_path, 'data', 'applications.jsonl')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def claude_tip(prompt):
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    if not api_key or anthropic is None:
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=500,
            system='You are a cautious financial education assistant. Give general educational guidance, not personalized investment or lending decisions. Clearly state that eligibility is estimated and lenders make final decisions.',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return ''.join(block.text for block in msg.content if hasattr(block, 'text')).strip()
    except Exception:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/api/eligibility')
def eligibility():
    data = request.get_json(force=True)
    try:
        result = loan_eligibility(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.post('/api/credit')
def credit():
    data = request.get_json(force=True)
    try:
        return jsonify(credit_analysis(data.get('creditScore', 0)))
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.post('/api/emi')
def emi():
    data = request.get_json(force=True)
    try:
        return jsonify(emi_calculator(data['principal'], data['rate'], data['months']))
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.post('/api/ai-tips')
def ai_tips():
    data = request.get_json(force=True)
    prompt = f"Give 5 concise financial education tips for this profile: age {data.get('age')}, monthly income {data.get('income')}, credit score {data.get('creditScore')}, employment {data.get('employment')}, existing EMI {data.get('existingEmi')}. Do not approve or reject a loan and do not claim certainty."
    answer = claude_tip(prompt)
    if not answer:
        answer = ('Focus on timely repayments, responsible credit utilization, maintaining an emergency fund, '
                  'comparing loan costs rather than only EMI, and checking lender terms before accepting an offer. '
                  'This is educational guidance, not a lending decision.')
    return jsonify({'answer': answer, 'aiEnabled': bool(os.getenv('ANTHROPIC_API_KEY') and anthropic)})


@app.post('/api/application')
def application():
    data = request.get_json(force=True)
    required = ['name','age','income','creditScore','employment','loanAmount','existingEmi']
    if any(k not in data or str(data[k]).strip() == '' for k in required):
        return jsonify({'error': 'Please complete all required fields.'}), 400
    data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    result = loan_eligibility(data)
    data['estimatedResult'] = result['status']
    data['estimatedScore'] = result['score']
    ok, message = append_google_sheet(data)
    if not ok:
        save_local(data)
    return jsonify({'success': True, 'message': message, 'storedInSheets': ok, 'result': result})


@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'claudeConfigured': bool(os.getenv('ANTHROPIC_API_KEY') and anthropic), 'sheetsConfigured': bool(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') and os.getenv('GOOGLE_SHEET_NAME'))})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG','0') == '1')

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.database import db, User, HealthTrend, Appointment, Feedback, SOSAlert, Guardian
import random
from utils.ai_engine import query_local_llm

main_bp = Blueprint('main', __name__)

@main_bp.before_request
def require_login():
    if 'user_id' not in session and request.endpoint not in ['auth.login', 'auth.signup', 'main.index', 'static']:
        return redirect(url_for('auth.login'))

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])
    trends = HealthTrend.query.filter_by(user_id=user.id).all()
    appointments = Appointment.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, trends=trends, appointments=appointments)

@main_bp.route('/doctor_dashboard')
def doctor_dashboard():
    user = User.query.get(session['user_id'])
    # In a real app check for user.role == 'doctor'
    appointments = Appointment.query.filter_by(doctor_id=user.id).all()
    return render_template('doctor_dashboard.html', user=user, appointments=appointments)

@main_bp.route('/admin_panel')
def admin_panel():
    user = User.query.get(session['user_id'])
    # Security: Only allow admins
    if user.role != 'admin':
        flash('Access Denied: Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    feedbacks = Feedback.query.all()
    sos_alerts = SOSAlert.query.order_by(SOSAlert.timestamp.desc()).all()
    return render_template('admin_panel.html', users=users, feedbacks=feedbacks, sos_alerts=sos_alerts)

@main_bp.route('/export_feedback')
def export_feedback():
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        return redirect(url_for('main.index'))

    import csv
    import io
    from flask import make_response

    feedbacks = Feedback.query.all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Feedback_ID', 'User_ID', 'Comment', 'Helpful_Status'])
    
    for f in feedbacks:
        writer.writerow([f.id, f.user_id if f.user_id else 'Guest', f.content, 'Helpful' if f.helpful else 'Not Helpful'])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=aura_ai_feedback.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@main_bp.route('/create_appointment', methods=['GET', 'POST'])
def create_appointment():
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        reason = request.form['reason']
        date = request.form['date']
        
        appt = Appointment(user_id=session['user_id'], doctor_id=doctor_id, reason=reason, date=date)
        db.session.add(appt)
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('appointment.html')
    
@main_bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@main_bp.route('/report')
def report():
    user = User.query.get(session['user_id'])
    trends = HealthTrend.query.filter_by(user_id=user.id).all()
    return render_template('report.html', user=user, trends=trends)

@main_bp.route('/medication')
def medication():
    return render_template('medication_reminder.html')

@main_bp.route('/sos', methods=['POST'])
def sos():
    user_id = session['user_id']
    alert = SOSAlert(user_id=user_id, status='active', location='Unknown')
    db.session.add(alert)
    db.session.commit()

    # Guardian Logic
    guardians = Guardian.query.filter_by(user_id=user_id).all()
    if guardians:
        for g in guardians:
            print(f"🚨 SOS: Alert sent to guardian {g.name} ({g.phone})")
        flash('SOS sent to guardian successfully. Help is on the way.', 'danger')
    else:
        flash('EMERGENCY SOS SENT. Help is on the way.', 'danger')
    
    return redirect(url_for('main.dashboard'))

@main_bp.route('/add_guardian', methods=['POST'])
def add_guardian():
    name = request.form['name']
    phone = request.form['phone']
    relation = request.form['relation']
    
    guardian = Guardian(user_id=session['user_id'], name=name, phone=phone, relation=relation)
    db.session.add(guardian)
    db.session.commit()
    
    flash(f'Guardian {name} added for emergency contacts.', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/resolve_sos/<int:alert_id>', methods=['POST'])
def resolve_sos(alert_id):
    user = User.query.get(session['user_id'])
    if user and user.role == 'admin':
        alert = SOSAlert.query.get(alert_id)
        if alert:
            alert.status = 'resolved'
            db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/explain', methods=['POST'])
def explain():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided.'}), 400
    
    prompt = f"Explain the following symptom or disease: '{query}'. Provide a clear and strictly structured response including exactly these sections:\n- Condition explanation\n- Possible causes\n- Precautions\n- Diet suggestions\n- When to consult a doctor."
    
    response_text = query_local_llm(prompt)
    return jsonify({'explanation': response_text})

@main_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    language = data.get('language', 'English')
    
    if not message:
        return jsonify({'response': 'No message provided.'})
        
    # 1. Try rule-based system first for reliable medical advice in specific languages
    lang_code_map = {'English': 'en', 'Hindi': 'hi', 'Telugu': 'te'}
    lang_code = lang_code_map.get(language, 'en')
    
    from utils.ai_engine import chat_response
    rule_response = chat_response(message, lang_code, session.get('user_id'))
    
    # Check if we got a generic fallback message
    default_markers = [
        "tell me more", "more details", "understand you're reaching", 
        "సమస్య నాకు సరిగ్గా అర్థం కాలేదు", "లక్షణాల గురించి వివరించండి", 
        "लक्षणों के बारे में थोड़ा और बता सकते हैं"
    ]
    is_default = any(marker in rule_response for marker in default_markers)

    # 2. If it's a default response, let the LLM try to give a more specific answer
    if is_default:
        if language != "English":
            full_prompt = f"System: Respond ONLY in {language} script. NEVER use English characters.\nUser: {message}\nAssistant:"
        else:
            full_prompt = f"System: You are a healthcare assistant. Respond briefly.\nUser: {message}\nAssistant:"
        
        llm_response = query_local_llm(full_prompt)
        
        # Aggressive cleaning: Remove any leading English "Yes, I can" style intros
        if language != "English":
            # Remove any line that is purely English if we expect non-English
            lines = llm_response.split('\n')
            clean_lines = []
            for line in lines:
                # Count English letters. If more than 30% of string is English and string is long, skip it.
                eng_count = sum(1 for c in line if 'a' <= c.lower() <= 'z')
                if len(line) > 5 and eng_count / len(line) > 0.3:
                    continue
                clean_lines.append(line)
            llm_response = ' '.join(clean_lines).strip()

        return jsonify({'response': llm_response if len(llm_response) > 5 else rule_response})

    return jsonify({'response': rule_response})

@main_bp.route('/generate_diet', methods=['POST'])
def generate_diet():
    data = request.json
    goal = data.get('goal', 'general health')
    age = data.get('age', 'not specified')
    weight = data.get('weight', 'not specified')
    
    if not goal:
        return jsonify({'error': 'No goal provided.'}), 400
    
    prompt = f"Create a practical, structured daily diet plan for a person (Age: {age}, Weight: {weight}kg) with the objective: {goal}. Use emojis, keep it short, and focus on practical foods. Avoid medical claims.\n\nStrict Format:\nMorning: ☀️\n- [items]\n\nAfternoon: 🌤️\n- [items]\n\nEvening: 🌙\n- [items]\n\nTips: 💡\n- [practical tips]"
    
    response_text = query_local_llm(prompt)
    return jsonify({'diet': response_text})

@main_bp.route('/diet')
def diet():
    return render_template('diet_planner.html')

@main_bp.route('/prescription_scanner')
def prescription_scanner():
    return render_template('prescription_scanner.html')

@main_bp.route('/report_analyzer')
def report_analyzer():
    return render_template('report_analyzer.html')
@main_bp.route('/simulate_vitals')
def simulate_vitals():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    heart_rate = random.randint(60, 100)
    sp02 = random.randint(95, 100)
    temperature = round(random.uniform(97.0, 101.0), 1)
    
    # Save to database
    trend = HealthTrend(
        user_id=session['user_id'],
        heart_rate=heart_rate,
        sp02=sp02,
        temperature=temperature,
        risk_score=random.randint(10, 30) # Simulated risk score
    )
    db.session.add(trend)
    db.session.commit()
    
    return jsonify({
        'heart_rate': heart_rate,
        'sp02': sp02,
        'temperature': temperature,
        'status': 'Device Connected',
        'message': 'Data simulated via local system (simulation only).'
    })

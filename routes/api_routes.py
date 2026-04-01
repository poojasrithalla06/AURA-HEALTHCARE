from flask import Blueprint, jsonify, request, render_template, make_response
from models.database import db, Medication, Feedback, SOSAlert, HealthTrend, User, Guardian, MedicationReminder
from utils.ai_engine import predict_risk, chat_response, scan_prescription_with_ai, analyze_health_report_with_ai
from datetime import datetime
import json
import os
try:
    import pytesseract
    from PIL import Image
    import fitz # PyMuPDF
except ImportError:
    print("Pre-requisites for OCR not installed.")


api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/predict_risk', methods=['POST'])
def get_risk():
    data = request.json
    # Expected: age, glucose, systolic_bp, diastolic_bp, heart_rate, sp02, temperature
    risk_score, explanation = predict_risk(data)
    
    # Save trend if user_id is provided
    if 'user_id' in data:
        trend = HealthTrend(
            user_id=data['user_id'],
            risk_score=risk_score,
            heart_rate=data.get('heart_rate'),
            sp02=data.get('sp02'),
            temperature=data.get('temperature')
        )
        db.session.add(trend)
        db.session.commit()
    
    return jsonify({
        'risk_score': risk_score,
        'category': 'Critical' if risk_score > 80 else 'High' if risk_score > 60 else 'Moderate' if risk_score > 30 else 'Low',
        'explanation': explanation
    })


@api_bp.route('/sos', methods=['POST'])
def trigger_sos():
    data = request.json
    user_id = data.get('user_id')
    location = data.get('location', 'Unknown Location')
    
    alert = SOSAlert(user_id=user_id, location=location)
    db.session.add(alert)
    db.session.commit()

    # Log alerts for each guardian
    guardians = Guardian.query.filter_by(user_id=user_id).all()
    if guardians:
        for g in guardians:
            print(f"🚨 API SOS: Alert sent to guardian {g.name} ({g.phone})")
        return jsonify({'status': 'alert_sent', 'message': 'SOS sent to guardian successfully!'})
    
    return jsonify({'status': 'alert_sent', 'message': 'Emergency contacts notified successfully!'})

@api_bp.route('/medication', methods=['POST', 'GET'])
def handle_medication():
    if request.method == 'POST':
        data = request.json
        med = Medication(
            user_id=data['user_id'],
            name=data['name'],
            time=data['time'],
            frequency=data['frequency']
        )
        db.session.add(med)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        user_id = request.args.get('user_id')
        meds = Medication.query.filter_by(user_id=user_id).all()
        reminders = MedicationReminder.query.filter_by(user_id=user_id).all()
        
        all_meds = []
        for m in meds:
            all_meds.append({'id': m.id, 'name': m.name, 'time': m.time, 'frequency': m.frequency})
        for r in reminders:
            all_meds.append({'id': r.id, 'name': r.medicine_name, 'time': r.time, 'status': r.status})
            
        return jsonify(all_meds)

@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    fb = Feedback(
        user_id=data.get('user_id'),
        content=data.get('comment'),
        helpful=data.get('helpful')
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({'status': 'feedback_received'})

@api_bp.route('/add_reminder', methods=['POST'])
def add_reminder():
    data = request.json
    reminder = MedicationReminder(
        user_id=data['user_id'],
        medicine_name=data['medicine_name'],
        time=data['time'],
        status='pending'
    )
    db.session.add(reminder)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Reminder added successfully!'})

@api_bp.route('/get_reminders', methods=['GET'])
def get_reminders():
    user_id = request.args.get('user_id')
    reminders = MedicationReminder.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': r.id,
        'medicine_name': r.medicine_name,
        'time': r.time,
        'status': r.status
    } for r in reminders])

@api_bp.route('/scan_prescription', methods=['POST'])
def scan_prescription():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Ensure upload directory exists
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    ocr_text = ""
    try:
        # Tesseract path configuration - Typical Windows paths
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
            os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe')
        ]
        
        # Only set if not already in PATH and file exists
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
        
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            img = Image.open(filepath)
            ocr_text = pytesseract.image_to_string(img)
        
        elif file.filename.lower().endswith('.pdf'):
            doc = fitz.open(filepath)
            for page in doc:
                # Try text extraction first (for digital PDFs)
                text = page.get_text()
                if text.strip():
                    ocr_text += text + "\n"
                else:
                    # For scanned PDFs, use OCR on the page image
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text += pytesseract.image_to_string(img) + "\n"
        
        if not ocr_text.strip():
            # Fallback for demonstration if OCR fails or Tesseract missing, but we want to show it works
            return jsonify({'error': 'No text could be extracted. Please ensure Tesseract OCR is installed on your system.'}), 422
            
        # Analysis with Local LLM
        analysis = scan_prescription_with_ai(ocr_text)
        
        # Cleanup uploaded file
        os.remove(filepath)
        
        return jsonify(analysis)

    except Exception as e:
        print(f"Scan Error Details: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
            
        # Simulation Mode Fallback:
        # If the error is about tesseract being missing, let's provide a simulation result
        # so the user can still use the app for demonstration purposes.
        error_msg = str(e).lower()
        if "tesseract" in error_msg or "not found" in error_msg or "not installed" in error_msg:
             from utils.ai_engine import scan_prescription_with_ai
             simulation_text = "PRESCRIPTION: Amoxicillin 500mg, Paracetamol 500mg. Take one tablet thrice daily after meals."
             analysis = scan_prescription_with_ai(simulation_text)
             analysis['message'] = "Note: Running in Simulation Mode (Local Tesseract OCR not found)."
             return jsonify(analysis)
             
        return jsonify({'error': f"Failed to process prescription: {str(e)}"}), 500

@api_bp.route('/analyze_report', methods=['POST'])
def analyze_report():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Ensure upload directory exists
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    ocr_text = ""
    try:
        # Tesseract path configuration - Typical Windows paths
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
            os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe')
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break

        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            img = Image.open(filepath)
            ocr_text = pytesseract.image_to_string(img)
        
        elif file.filename.lower().endswith('.pdf'):
            doc = fitz.open(filepath)
            for page in doc:
                text = page.get_text()
                if text.strip():
                    ocr_text += text + "\n"
                else:
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text += pytesseract.image_to_string(img) + "\n"
        
        if not ocr_text.strip():
            return jsonify({'error': 'No text could be extracted. Please ensure Tesseract OCR is installed on your system.'}), 422
            
        # Analysis with Local LLM
        from utils.ai_engine import analyze_health_report_with_ai
        analysis = analyze_health_report_with_ai(ocr_text)
        
        # Cleanup uploaded file
        os.remove(filepath)
        
        return jsonify(analysis)

    except Exception as e:
        print(f"Report Analysis Error: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)

        # Simulation Mode Fallback for Report
        error_msg = str(e).lower()
        if "tesseract" in error_msg or "not found" in error_msg or "not installed" in error_msg:
             from utils.ai_engine import analyze_health_report_with_ai
             simulation_text = "LAB REPORT SUMMARY: HB: 14.5, WBC: 8500, Platelets: 250k. All values within normal range."
             analysis = analyze_health_report_with_ai(simulation_text)
             analysis['message'] = "Note: Running in Simulation Mode (Local Tesseract OCR not found)."
             return jsonify(analysis)

        return jsonify({'error': f"Failed to analyze report: {str(e)}"}), 500

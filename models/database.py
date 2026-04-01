from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # user, doctor, admin
    health_data = db.relationship('HealthTrend', backref='user', lazy=True)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    medications = db.relationship('Medication', backref='user', lazy=True)
    reminders = db.relationship('MedicationReminder', backref='user', lazy=True)
    guardians = db.relationship('Guardian', backref='user', lazy=True)

class MedicationReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(20), nullable=False) # e.g., "14:30"
    status = db.Column(db.String(20), default='pending') # pending, taken, missed

class Guardian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relation = db.Column(db.String(50), nullable=False)

class HealthTrend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    heart_rate = db.Column(db.Integer)
    blood_pressure = db.Column(db.String(20))
    sp02 = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    risk_score = db.Column(db.Integer) # 0-100

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(20)) # e.g., "08:00 AM"
    frequency = db.Column(db.String(50)) # e.g., "Daily", "Weekly"

class SOSAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    content = db.Column(db.Text)
    helpful = db.Column(db.Boolean, default=True)

from dotenv import load_dotenv
load_dotenv(override=True)

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)

def utc_now():
    """Returns current UTC datetime as a naive datetime object for cross-DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ----------------- DATABASE MODELS ----------------- #

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="Patient")
    otp = db.Column(db.String(10), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    registered_at = db.Column(db.DateTime, default=utc_now)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

class Bill(db.Model):
    __tablename__ = 'bills'
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=utc_now)
    paid_at = db.Column(db.DateTime, nullable=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    doctor_name = db.Column(db.String(100), nullable=True)
    patient_name = db.Column(db.String(100), nullable=False)
    appointment_date = db.Column(db.String(50), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Confirmed")
    created_at = db.Column(db.DateTime, default=utc_now)

# ----------------- AUTH DECORATOR ----------------- #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "Authentication required."}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- PAGE ROUTES ----------------- #

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html', user_name=session.get('user_name'), user_role=session.get('user_role'))

@app.route('/patients')
@login_required
def patients_page():
    return render_template('patients.html')

@app.route('/doctors')
@login_required
def doctors_page():
    return render_template('doctors.html')

@app.route('/prescriptions')
@login_required
def prescriptions_page():
    return render_template('prescriptions.html')

@app.route('/billing')
@login_required
def billing_page():
    return render_template('billing.html')

# ----------------- API ENDPOINTS ----------------- #

def send_otp_email(recipient, recipient_name, otp):
    """Send a real OTP email through the configured Gmail SMTP account (supports port 587 TLS & port 465 SSL)."""
    sender_email = (app.config.get("SMTP_EMAIL") or "").strip()
    sender_password = (app.config.get("SMTP_PASSWORD") or "").replace(" ", "").strip()

    if not sender_email or not sender_password:
        raise RuntimeError("Gmail SMTP is not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env.")
    if sender_email == "your_email@gmail.com" or sender_password == "your_app_password":
        raise RuntimeError("Replace the Gmail SMTP placeholder values in .env with a real Gmail address and App Password.")

    message = MIMEMultipart("alternative")
    message["From"] = f"CarePulse Hospital <{sender_email}>"
    message["To"] = recipient
    message["Subject"] = f"{otp} is your CarePulse verification code"

    text_body = (
        f"Hello {recipient_name},\n\n"
        f"Your CarePulse verification code is: {otp}\n"
        "It will expire in 10 minutes.\n\n"
        "Thank you,\nCarePulse Hospital"
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px;">
        <h2 style="color: #1e1b4b; margin-top: 0;">CarePulse Hospital Verification</h2>
        <p style="color: #334155;">Hello <strong>{recipient_name}</strong>,</p>
        <p style="color: #334155;">Use the verification code below to complete your registration:</p>
        <div style="background: #eef2ff; color: #312e81; font-size: 28px; font-weight: bold; letter-spacing: 6px; text-align: center; padding: 16px; border-radius: 8px; margin: 20px 0;">
            {otp}
        </div>
        <p style="color: #64748b; font-size: 13px;">This code will expire in <strong>10 minutes</strong>. If you did not request this code, please ignore this email.</p>
    </div>
    """

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    smtp_server = app.config["SMTP_SERVER"]
    smtp_port = int(app.config["SMTP_PORT"])

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_server, 465, timeout=20) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, message.as_string())
    else:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, message.as_string())


@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    provided_name = (data.get("name") or "").strip()
    raw_password = data.get("password")
    raw_user_id = (data.get("user_id") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None

    if not email:
        return jsonify({"status": "error", "message": "Email address is required."}), 400

    # Cryptographically secure 6-digit OTP generation with 10-minute validity
    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_expiry = utc_now() + timedelta(minutes=10)

    user = User.query.filter_by(email=email).first()
    if user:
        if user.is_verified:
            return jsonify({"status": "error", "message": "Account already verified. Please log in."}), 400
        if provided_name:
            user.name = provided_name
        if raw_user_id:
            user.user_id = raw_user_id
        if phone:
            user.phone = phone
        user.otp = otp
        user.otp_expiry = otp_expiry
        if raw_password:
            user.password = generate_password_hash(raw_password)
        effective_name = user.name
    else:
        if not raw_password:
            return jsonify({"status": "error", "message": "Password is required for registration."}), 400

        effective_name = provided_name or "User"
        user = User(
            name=effective_name,
            user_id=raw_user_id,
            phone=phone,
            email=email,
            password=generate_password_hash(raw_password),
            role=data.get("role", "Patient"),
            otp=otp,
            otp_expiry=otp_expiry,
            is_verified=False
        )
        db.session.add(user)

    try:
        send_otp_email(email, effective_name, otp)
        db.session.commit()
    except smtplib.SMTPAuthenticationError:
        db.session.rollback()
        app.logger.exception("Gmail SMTP authentication failed for %s", app.config.get("SMTP_EMAIL"))
        return jsonify({
            "status": "error",
            "message": "Gmail rejected the SMTP credentials. Check SMTP_EMAIL and SMTP_PASSWORD in .env.",
        }), 503
    except RuntimeError as error:
        db.session.rollback()
        app.logger.error("OTP email configuration error: %s", error)
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 503
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to send OTP email to %s", email)
        return jsonify({
            "status": "error",
            "message": "Could not send verification email. Check your internet connection and Gmail SMTP settings.",
        }), 503

    return jsonify({
        "status": "success",
        "message": "Verification code sent to your email address."
    })


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    otp_input = (data.get("otp") or "").strip()

    user = User.query.filter_by(email=email).first()
    if not user or user.otp != otp_input:
        return jsonify({"status": "error", "message": "Invalid verification code."}), 400

    if user.otp_expiry and utc_now() > user.otp_expiry:
        return jsonify({"status": "error", "message": "Verification code has expired. Please request a new one."}), 400

    user.is_verified = True
    user.otp = None
    user.otp_expiry = None
    db.session.commit()

    session['user_email'] = user.email
    session['user_name'] = user.name
    session['user_role'] = user.role

    return jsonify({
        "status": "success",
        "message": "Verification successful!",
        "user": {"name": user.name, "role": user.role}
    })


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.json or {}
    identifier = (data.get("email") or data.get("phone") or "").strip().lower()
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"status": "error", "message": "Email/Phone and password are required."}), 400

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if user and check_password_hash(user.password, password):
        if not user.is_verified:
            return jsonify({"status": "error", "message": "Please verify your email address first."}), 400

        session['user_email'] = user.email
        session['user_name'] = user.name
        session['user_role'] = user.role

        return jsonify({
            "status": "success",
            "message": "Login successful!",
            "user": {"name": user.name, "role": user.role}
        })

    return jsonify({"status": "error", "message": "Invalid credentials or password."}), 400


# --- Dashboard & Analytics API ---
@app.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_prescriptions = Prescription.query.count()
    total_revenue = db.session.query(db.func.sum(Bill.amount)).scalar() or 0.0

    dept_counts = db.session.query(Patient.department, db.func.count(Patient.id)).group_by(Patient.department).all()
    dept_results = [{"department": dept, "count": count} for dept, count in dept_counts]

    return jsonify({
        "metrics": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_prescriptions": total_prescriptions,
            "total_revenue": float(total_revenue)
        },
        "departments": dept_results
    })


# --- Patient Management with Server-Side Pagination & Search ---
@app.route('/api/patients', methods=['GET', 'POST'])
@login_required
def manage_patients():
    if request.method == 'POST':
        data = request.json or {}
        name = (data.get('name') or '').strip()
        department = (data.get('department') or '').strip()

        if not name or not department:
            return jsonify({"status": "error", "message": "Patient Name and Department are required."}), 400

        new_patient = Patient(
            name=name,
            department=department,
            age=data.get('age'),
            gender=data.get('gender'),
            phone=(data.get('phone') or '').strip() or None
        )
        db.session.add(new_patient)
        db.session.commit()
        return jsonify({"status": "success", "id": new_patient.id})

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 5, type=int)
    search_query = request.args.get('search', '').strip()

    query = Patient.query
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Patient.name.like(search_filter),
                Patient.department.like(search_filter),
                Patient.phone.like(search_filter)
            )
        )

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    patient_list = [{
        "id": p.id,
        "name": p.name,
        "department": p.department,
        "age": p.age,
        "gender": p.gender,
        "phone": p.phone
    } for p in pagination.items]

    return jsonify({
        "patients": patient_list,
        "total_records": pagination.total,
        "total_pages": pagination.pages,
        "current_page": pagination.page,
        "limit": limit
    })


# --- Doctors Directory ---
@app.route('/api/doctors', methods=['GET'])
@login_required
def get_doctors():
    doctors = Doctor.query.all()
    return jsonify([{
        "id": d.id,
        "name": d.name,
        "department": d.department,
        "email": d.email
    } for d in doctors])


# --- Appointments Booking API ---
@app.route('/api/appointments', methods=['POST'])
@login_required
def book_appointment():
    data = request.json or {}
    patient_name = (data.get("patient_name") or "").strip()
    appointment_date = (data.get("appointment_date") or "").strip()
    time_slot = (data.get("time_slot") or "").strip()
    doctor_id = data.get("doctor_id")
    doctor_name = (data.get("doctor_name") or "").strip()

    if not patient_name or not appointment_date or not time_slot:
        return jsonify({"status": "error", "message": "Patient name, date, and time slot are required."}), 400

    appointment = Appointment(
        doctor_id=int(doctor_id) if doctor_id else None,
        doctor_name=doctor_name or "Specialist",
        patient_name=patient_name,
        appointment_date=appointment_date,
        time_slot=time_slot,
        status="Confirmed"
    )
    db.session.add(appointment)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Appointment confirmed for {patient_name} on {appointment_date} ({time_slot})!",
        "id": appointment.id
    })


# --- Prescriptions API ---
@app.route('/api/prescriptions', methods=['GET', 'POST'])
@login_required
def manage_prescriptions():
    if request.method == 'POST':
        data = request.json or {}
        patient_name = (data.get('patient_name') or '').strip()
        details = (data.get('details') or '').strip()

        if not patient_name or not details:
            return jsonify({"status": "error", "message": "Patient Name and Details/Medicines are required."}), 400

        new_prescription = Prescription(
            patient_name=patient_name,
            details=details
        )
        db.session.add(new_prescription)
        db.session.commit()
        return jsonify({"status": "success", "id": new_prescription.id})

    prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).all()
    return jsonify([{
        "id": pr.id,
        "patient_name": pr.patient_name,
        "details": pr.details,
        "date": pr.created_at.strftime('%Y-%m-%d')
    } for pr in prescriptions])


# --- Billing & Payments API ---
@app.route('/api/billing', methods=['GET', 'POST'])
@login_required
def manage_billing():
    if request.method == 'POST':
        data = request.json or {}
        patient_name = (data.get('patient_name') or '').strip()
        if not patient_name:
            return jsonify({"status": "error", "message": "Patient name is required."}), 400

        try:
            amount = float(data.get('amount', 0.0))
            if amount <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Amount must be a positive number."}), 400

        new_bill = Bill(
            patient_name=patient_name,
            amount=amount
        )
        db.session.add(new_bill)
        db.session.commit()
        return jsonify({"status": "success", "id": new_bill.id})

    bills = Bill.query.order_by(Bill.created_at.desc()).all()
    return jsonify([{
        "id": b.id,
        "patient_name": b.patient_name,
        "amount": b.amount,
        "status": b.status,
        "date": b.created_at.strftime('%Y-%m-%d')
    } for b in bills])


@app.route('/api/billing/pay/<int:bill_id>', methods=['POST'])
@login_required
def pay_bill(bill_id):
    bill = db.get_or_404(Bill, bill_id)
    bill.status = "Paid"
    bill.paid_at = utc_now()
    db.session.commit()
    return jsonify({"status": "success", "message": "Payment successful!"})


def seed_initial_doctors():
    """Seeds starter doctor profiles if the directory is empty."""
    if Doctor.query.count() == 0:
        sample_doctors = [
            Doctor(name="Dr. Sarah Jenkins", department="Cardiology", email="sarah.jenkins@carepulse.com"),
            Doctor(name="Dr. Marcus Vance", department="Neurology", email="marcus.vance@carepulse.com"),
            Doctor(name="Dr. Priya Sharma", department="Pediatrics", email="priya.sharma@carepulse.com"),
            Doctor(name="Dr. David Chen", department="Orthopedics", email="david.chen@carepulse.com"),
            Doctor(name="Dr. Elena Rostova", department="General Medicine", email="elena.rostova@carepulse.com")
        ]
        db.session.add_all(sample_doctors)
        db.session.commit()
        print("[INFO] Seeded default doctors directory.")


# Startup execution
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_initial_doctors()
    app.run(debug=True, port=5000)
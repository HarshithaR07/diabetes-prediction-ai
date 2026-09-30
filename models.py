from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()


# =========================================================
# USER
# =========================================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    age = db.Column(
        db.Integer
    )

    gender = db.Column(
        db.String(10)
    )

    predictions = db.relationship(
        'Prediction',
        backref='user',
        lazy=True
    )

    medications = db.relationship(
        'Medication',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    appointments = db.relationship(
        'Appointment',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    notifications = db.relationship(
        'Notification',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )


# =========================================================
# PREDICTION
# =========================================================

class Prediction(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------------------
    # Patient information at the time of prediction
    # -----------------------------------------------------

    year = db.Column(
        db.Integer
    )

    gender = db.Column(
        db.String(20)
    )

    age = db.Column(
        db.Integer
    )

    location = db.Column(
        db.String(100)
    )

    race = db.Column(
        db.String(50)
    )

    # -----------------------------------------------------
    # Health conditions
    # -----------------------------------------------------

    hypertension = db.Column(
        db.Integer
    )

    heart_disease = db.Column(
        db.Integer
    )

    smoking_history = db.Column(
        db.String(50)
    )

    # -----------------------------------------------------
    # Health measurements
    # -----------------------------------------------------

    glucose = db.Column(
        db.Float
    )

    bmi = db.Column(
        db.Float
    )

    hbA1c_level = db.Column(
        db.Float
    )

    # Kept for compatibility with the existing project
    blood_pressure = db.Column(
        db.Float
    )

    # -----------------------------------------------------
    # AI prediction
    # -----------------------------------------------------

    risk_tier = db.Column(
        db.String(20)
    )

    probability = db.Column(
        db.Float
    )


# =========================================================
# MEDICATION
# =========================================================

class Medication(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    medicine_name = db.Column(
        db.String(150),
        nullable=False
    )

    dosage = db.Column(
        db.String(100)
    )

    time = db.Column(
        db.String(50)
    )

    notes = db.Column(
        db.String(300)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# DOCTOR
# =========================================================

class Doctor(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    specialization = db.Column(
        db.String(200),
        nullable=False
    )

    hospital = db.Column(
        db.String(200),
        nullable=False
    )

    phone = db.Column(
        db.String(30)
    )

    appointments = db.relationship(
        'Appointment',
        backref='doctor',
        lazy=True
    )


# =========================================================
# APPOINTMENT
# =========================================================

class Appointment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctor.id"),
        nullable=True
    )

    doctor_name = db.Column(
        db.String(200),
        nullable=False
    )

    hospital = db.Column(
        db.String(200),
        nullable=False
    )

    appointment_date = db.Column(
        db.String(20),
        nullable=False
    )

    appointment_time = db.Column(
        db.String(20),
        nullable=False
    )

    purpose = db.Column(
        db.String(500)
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------------------
    # REAL APPOINTMENT PROVIDER INFORMATION
    # -----------------------------------------------------

    provider = db.Column(
        db.String(50),
        default="local"
    )

    external_provider_id = db.Column(
        db.String(150)
    )

    external_booking_id = db.Column(
        db.String(150)
    )

    external_status = db.Column(
        db.String(50)
    )

    # -----------------------------------------------------
    # PRACTO / EXTERNAL PROVIDER CONSENT
    # -----------------------------------------------------

    practo_consent = db.Column(
        db.Boolean,
        default=False
    )

    practo_consent_at = db.Column(
        db.DateTime,
        nullable=True
    )


# =========================================================
# NOTIFICATION
# =========================================================

class Notification(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.String(500),
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        default='general'
    )

    reminder_time = db.Column(
        db.DateTime,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    is_sent = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
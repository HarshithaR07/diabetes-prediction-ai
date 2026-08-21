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

    glucose = db.Column(
        db.Float
    )

    bmi = db.Column(
        db.Float
    )

    blood_pressure = db.Column(
        db.Float
    )

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
# APPOINTMENT
# =========================================================

class Appointment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
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
        default="Booked"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
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
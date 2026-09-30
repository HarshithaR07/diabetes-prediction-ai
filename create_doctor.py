import sqlite3
import os
from werkzeug.security import generate_password_hash


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "instance",
    "database.db"
)


# =========================================================
# DOCTOR DETAILS
# =========================================================

name = "Dr. Ananya Rao"
email = "ananya.rao@diabetescare.com"
password = "doctor123"

specialization = "Diabetologist"
hospital = "Diabetes Care Hospital"
phone = "9876543210"


# =========================================================
# CONNECT
# =========================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# =========================================================
# CHECK EXISTING DOCTOR
# =========================================================

cursor.execute(
    "SELECT id FROM doctor WHERE email = ?",
    (email,)
)

existing_doctor = cursor.fetchone()


if existing_doctor:

    print("Doctor already exists.")
    print("Doctor ID:", existing_doctor[0])

else:

    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO doctor
        (
            name,
            email,
            password,
            specialization,
            hospital,
            phone,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        name,
        email,
        hashed_password,
        specialization,
        hospital,
        phone
    ))

    conn.commit()

    print("Doctor created successfully!")


# =========================================================
# DISPLAY LOGIN DETAILS
# =========================================================

print("\n========================================")
print("DOCTOR ACCOUNT")
print("========================================")
print("Name          :", name)
print("Email         :", email)
print("Password      :", password)
print("Specialization:", specialization)
print("Hospital      :", hospital)
print("Phone         :", phone)
print("========================================")


# =========================================================
# CLOSE
# =========================================================

conn.close()
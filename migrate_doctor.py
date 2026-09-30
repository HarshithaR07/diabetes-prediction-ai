import sqlite3
import os


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "instance",
    "database.db"
)


print("Database:", DB_PATH)


# =========================================================
# CONNECT TO DATABASE
# =========================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# =========================================================
# 1. CREATE DOCTOR TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS doctor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    specialization VARCHAR(150),
    hospital VARCHAR(200),
    phone VARCHAR(30),
    created_at DATETIME
)
""")


print("Doctor table checked/created.")


# =========================================================
# 2. CHECK APPOINTMENT TABLE
# =========================================================

cursor.execute("PRAGMA table_info(appointment)")

columns = cursor.fetchall()

column_names = [
    column[1]
    for column in columns
]


# =========================================================
# 3. ADD doctor_id IF IT DOES NOT EXIST
# =========================================================

if "doctor_id" not in column_names:

    cursor.execute("""
    ALTER TABLE appointment
    ADD COLUMN doctor_id INTEGER
    """)

    print("doctor_id column added to appointment table.")

else:

    print("doctor_id column already exists.")


# =========================================================
# 4. SAVE CHANGES
# =========================================================

conn.commit()


# =========================================================
# 5. VERIFY
# =========================================================

print("\nDoctor table:")

cursor.execute("PRAGMA table_info(doctor)")

for column in cursor.fetchall():
    print(column)


print("\nAppointment table:")

cursor.execute("PRAGMA table_info(appointment)")

for column in cursor.fetchall():
    print(column)


# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()

print("\n======================================")
print("DATABASE UPDATE COMPLETED SUCCESSFULLY")
print("======================================")
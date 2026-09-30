import sqlite3
import os


DATABASE_PATH = os.path.join(
    "instance",
    "database.db"
)


def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_definition
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if column_name not in existing_columns:

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )

        print(
            f"Added column: {column_name}"
        )

    else:

        print(
            f"Already exists: {column_name}"
        )


print("=" * 60)
print("Practo Appointment Database Migration")
print("=" * 60)


if not os.path.exists(DATABASE_PATH):

    print(
        f"\nDatabase not found:\n{DATABASE_PATH}"
    )

    print(
        "\nMake sure this script is inside your "
        "diabetes_project folder."
    )

    raise SystemExit(1)


connection = sqlite3.connect(
    DATABASE_PATH
)

cursor = connection.cursor()


# ---------------------------------------------------------
# CHECK APPOINTMENT TABLE
# ---------------------------------------------------------

cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='appointment'
    """
)

appointment_table = cursor.fetchone()


if not appointment_table:

    print(
        "\nAppointment table was not found."
    )

    connection.close()

    raise SystemExit(1)


# ---------------------------------------------------------
# REAL PROVIDER INFORMATION
# ---------------------------------------------------------

add_column_if_missing(
    cursor,
    "appointment",
    "provider",
    "VARCHAR(50) DEFAULT 'local'"
)


add_column_if_missing(
    cursor,
    "appointment",
    "external_provider_id",
    "VARCHAR(150)"
)


add_column_if_missing(
    cursor,
    "appointment",
    "external_booking_id",
    "VARCHAR(150)"
)


add_column_if_missing(
    cursor,
    "appointment",
    "external_status",
    "VARCHAR(50)"
)


# ---------------------------------------------------------
# COMMIT
# ---------------------------------------------------------

connection.commit()

connection.close()


print()
print("=" * 60)
print("Migration completed successfully.")
print("=" * 60)

print()
print("New appointment fields:")
print("1. provider")
print("2. external_provider_id")
print("3. external_booking_id")
print("4. external_status")

print()
print(
    "Existing appointment records were not deleted."
)

print(
    "Do NOT run the Flask application yet."
)
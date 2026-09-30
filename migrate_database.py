import os
import shutil
from sqlalchemy import inspect, text

from app import app, db


# ---------------------------------------------------------
# DATABASE BACKUP
# ---------------------------------------------------------

database_path = os.path.join(
    app.instance_path,
    "database.db"
)

backup_path = os.path.join(
    app.instance_path,
    "database_backup_before_monthly_report.db"
)

if os.path.exists(database_path):
    shutil.copy2(
        database_path,
        backup_path
    )

    print("Database backup created:")
    print(backup_path)


# ---------------------------------------------------------
# ADD NEW PREDICTION COLUMNS
# ---------------------------------------------------------

new_columns = {
    "year": "INTEGER",
    "gender": "VARCHAR(20)",
    "age": "INTEGER",
    "location": "VARCHAR(100)",
    "race": "VARCHAR(50)",
    "hypertension": "INTEGER",
    "heart_disease": "INTEGER",
    "smoking_history": "VARCHAR(50)",
    "hbA1c_level": "FLOAT"
}


with app.app_context():

    inspector = inspect(db.engine)

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("prediction")
    }

    print("\nExisting Prediction columns:")
    print(existing_columns)

    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:

            sql = text(
                f'ALTER TABLE prediction '
                f'ADD COLUMN "{column_name}" {column_type}'
            )

            db.session.execute(sql)

            print(
                f"Added column: {column_name}"
            )

        else:

            print(
                f"Already exists: {column_name}"
            )

    db.session.commit()

    print("\nDatabase migration completed successfully.")
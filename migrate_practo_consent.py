from app import app
from models import db
from sqlalchemy import inspect, text


with app.app_context():

    print("=" * 60)
    print("Practo Consent Database Migration")
    print("=" * 60)

    inspector = inspect(db.engine)

    tables = inspector.get_table_names()

    if "appointment" not in tables:
        print()
        print("ERROR: appointment table does not exist.")
        print("Please make sure your database has been initialized.")
        print()

    else:

        columns = {
            column["name"]
            for column in inspector.get_columns("appointment")
        }

        # -------------------------------------------------
        # ADD PRACTO CONSENT
        # -------------------------------------------------

        if "practo_consent" not in columns:

            db.session.execute(
                text(
                    """
                    ALTER TABLE appointment
                    ADD COLUMN practo_consent BOOLEAN
                    DEFAULT 0
                    """
                )
            )

            print("Added column: practo_consent")

        else:

            print("Column already exists: practo_consent")

        # -------------------------------------------------
        # ADD PRACTO CONSENT TIMESTAMP
        # -------------------------------------------------

        if "practo_consent_at" not in columns:

            db.session.execute(
                text(
                    """
                    ALTER TABLE appointment
                    ADD COLUMN practo_consent_at DATETIME
                    """
                )
            )

            print("Added column: practo_consent_at")

        else:

            print("Column already exists: practo_consent_at")

        # -------------------------------------------------
        # SAVE CHANGES
        # -------------------------------------------------

        db.session.commit()

        print()
        print("Migration completed successfully.")
        print()
        print("New appointment fields:")
        print("1. practo_consent")
        print("2. practo_consent_at")
        print()
        print("Existing appointment records were not deleted.")
        print()
        print("Do NOT run Flask yet.")
        print("=" * 60)
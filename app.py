from exercise_data import EXERCISE_VIDEOS

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    session
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models import db, User, Prediction

from meal_data import MEAL_PLANS
from meal_translations import translate_dish
from chatbot_logic import get_chatbot_response
from pdf_generator import generate_health_report
from translations import TRANSLATIONS
from shap_explainer import get_shap_explanation

import joblib
import numpy as np
import random
import os

from datetime import datetime

from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "change-this-to-a-random-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# =========================================================
# LOGIN MANAGER
# =========================================================

login_manager = LoginManager()

login_manager.login_view = "login"

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

model = joblib.load(
    "model/diabetes_model.pkl"
)

scaler = joblib.load(
    "model/scaler.pkl"
)


# =========================================================
# TRANSLATION
# =========================================================

def get_t():

    lang = session.get(
        "lang",
        "en"
    )

    if lang not in TRANSLATIONS:
        lang = "en"

    return TRANSLATIONS[lang], lang


# =========================================================
# RISK FUNCTIONS
# =========================================================

def get_risk_tier(probability):

    if probability < 0.33:
        return "Low"

    elif probability < 0.66:
        return "Medium"

    else:
        return "High"


def get_risk_tier_translated(
    risk_tier,
    t
):

    mapping = {

        "Low": t["risk_low"],

        "Medium": t["risk_medium"],

        "High": t["risk_high"]

    }

    return mapping.get(
        risk_tier,
        risk_tier
    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

def get_recommendations(
    inputs,
    t
):

    tips = []

    (
        pregnancies,
        glucose,
        bp,
        skin,
        insulin,
        bmi,
        dpf,
        age
    ) = inputs

    if glucose > 140:

        tips.append(
            t["tip_glucose"]
        )

    if bmi > 25:

        tips.append(
            t["tip_bmi"]
        )

    if bp > 80:

        tips.append(
            t["tip_bp"]
        )

    if insulin > 150:

        tips.append(
            t["tip_insulin"]
        )

    if age > 45:

        tips.append(
            t["tip_age"]
        )

    if not tips:

        tips.append(
            t["tip_healthy"]
        )

    return tips


# =========================================================
# BMI CATEGORY TRANSLATION
# =========================================================

def get_bmi_category(bmi):

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal Weight"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obese"


def get_bmi_category_translated(
    category,
    t
):

    mapping = {

        "Underweight":
            t["bmi_underweight"],

        "Normal Weight":
            t["bmi_normal"],

        "Overweight":
            t["bmi_overweight"],

        "Obese":
            t["bmi_obese"]

    }

    return mapping.get(
        category,
        category
    )


# =========================================================
# LOCAL NUMBERS
# =========================================================

KANNADA_DIGITS = str.maketrans(
    "0123456789",
    "೦೧೨೩೪೫೬೭೮೯"
)

HINDI_DIGITS = str.maketrans(
    "0123456789",
    "०१२३४५६७८९"
)


@app.template_filter("localnum")
def localnum(value):

    lang = session.get(
        "lang",
        "en"
    )

    s = str(value)

    if lang == "kn":

        return s.translate(
            KANNADA_DIGITS
        )

    elif lang == "hi":

        return s.translate(
            HINDI_DIGITS
        )

    return s


# =========================================================
# DATE FORMAT
# =========================================================

def format_date_localized(
    dt,
    t,
    lang
):

    day = str(
        dt.day
    ).zfill(2)

    month_key = (
        f"month_{dt.month:02d}"
    )

    month_name = t.get(
        month_key,
        dt.strftime("%B")
    )

    year = str(
        dt.year
    )

    time_part = dt.strftime(
        "%H:%M"
    )

    date_str = (
        f"{day}-{month_name}-{year} "
        f"{time_part}"
    )

    if lang == "kn":

        date_str = date_str.translate(
            KANNADA_DIGITS
        )

    elif lang == "hi":

        date_str = date_str.translate(
            HINDI_DIGITS
        )

    return date_str


# =========================================================
# LANGUAGE ROUTE
# =========================================================

@app.route(
    "/set-language/<lang_code>"
)
def set_language(lang_code):

    if lang_code in TRANSLATIONS:

        session["lang"] = lang_code

    return redirect(
        request.referrer
        or url_for("home")
    )


# =========================================================
# SIGNUP
# =========================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        age = request.form.get(
            "age",
            ""
        )

        gender = request.form.get(
            "gender",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill all required fields."
            )

            return redirect(
                url_for("signup")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "Email already registered. Please login."
            )

            return redirect(
                url_for("signup")
            )

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            age=age,
            gender=gender
        )

        db.session.add(
            new_user
        )

        db.session.commit()

        flash(
            "Account created successfully! Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "signup.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for("home")
            )

        else:

            flash(
                "Invalid email or password."
            )

            return redirect(
                url_for("login")
            )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    session.pop(
        "appointments",
        None
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
@login_required
def home():

    t, lang = get_t()

    return render_template(
        "index.html",
        t=t,
        current_lang=lang
    )


# =========================================================
# DIABETES PREDICTION
# =========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
@login_required
def predict():

    try:

        pregnancies = float(
            request.form["pregnancies"]
        )

        glucose = float(
            request.form["glucose"]
        )

        bp = float(
            request.form["bloodpressure"]
        )

        skin = float(
            request.form["skinthickness"]
        )

        insulin = float(
            request.form["insulin"]
        )

        bmi = float(
            request.form["bmi"]
        )

        dpf = float(
            request.form["dpf"]
        )

        age = float(
            request.form["age"]
        )

        input_data = np.array([
            [
                pregnancies,
                glucose,
                bp,
                skin,
                insulin,
                bmi,
                dpf,
                age
            ]
        ])

        input_scaled = scaler.transform(
            input_data
        )

        probability = model.predict_proba(
            input_scaled
        )[0][1]

        risk_tier = get_risk_tier(
            probability
        )

        t, lang = get_t()

        recommendations = get_recommendations(
            [
                pregnancies,
                glucose,
                bp,
                skin,
                insulin,
                bmi,
                dpf,
                age
            ],
            t
        )

        risk_tier_display = get_risk_tier_translated(
            risk_tier,
            t
        )

        shap_contributions = get_shap_explanation(
            input_scaled,
            t
        )

        new_prediction = Prediction(
            user_id=current_user.id,
            glucose=glucose,
            bmi=bmi,
            blood_pressure=bp,
            risk_tier=risk_tier,
            probability=round(
                float(probability) * 100,
                2
            )
        )

        db.session.add(
            new_prediction
        )

        db.session.commit()

        return render_template(
            "result.html",
            risk_tier=risk_tier,
            risk_tier_display=risk_tier_display,
            probability=round(
                float(probability) * 100,
                2
            ),
            recommendations=recommendations,
            shap_contributions=shap_contributions,
            t=t
        )

    except Exception as e:

        return f"Error: {str(e)}"


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    t, lang = get_t()

    user_predictions = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date
    ).all()

    dates = [
        p.date.strftime("%d-%b-%Y")
        for p in user_predictions
    ]

    glucose_values = [
        p.glucose
        for p in user_predictions
    ]

    bmi_values = [
        p.bmi
        for p in user_predictions
    ]

    risk_probabilities = [
        p.probability
        for p in user_predictions
    ]

    risk_tiers_translated = [
        get_risk_tier_translated(
            p.risk_tier,
            t
        )
        for p in user_predictions
    ]

    table_dates = [
        format_date_localized(
            p.date,
            t,
            lang
        )
        for p in user_predictions
    ]

    return render_template(
        "dashboard.html",
        predictions=user_predictions,
        dates=dates,
        glucose_values=glucose_values,
        bmi_values=bmi_values,
        risk_probabilities=risk_probabilities,
        risk_tiers_translated=risk_tiers_translated,
        table_dates=table_dates,
        t=t
    )


# =========================================================
# MEAL PLAN
# =========================================================

@app.route(
    "/meal-plan/<risk_tier>"
)
@login_required
def meal_plan(risk_tier):

    t, lang = get_t()

    if risk_tier not in MEAL_PLANS:

        risk_tier = "Low"

    day_keys = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"
    ]

    weekly_plan = []

    for day_key in day_keys:

        breakfast_dish = random.choice(
            MEAL_PLANS[risk_tier]["Breakfast"]
        )

        lunch_dish = random.choice(
            MEAL_PLANS[risk_tier]["Lunch"]
        )

        dinner_dish = random.choice(
            MEAL_PLANS[risk_tier]["Dinner"]
        )

        weekly_plan.append({

            "day": t[day_key],

            "breakfast": translate_dish(
                breakfast_dish,
                lang
            ),

            "lunch": translate_dish(
                lunch_dish,
                lang
            ),

            "dinner": translate_dish(
                dinner_dish,
                lang
            )

        })

    risk_tier_display = get_risk_tier_translated(
        risk_tier,
        t
    )

    return render_template(
        "meal_plan.html",
        risk_tier=risk_tier,
        risk_tier_display=risk_tier_display,
        weekly_plan=weekly_plan,
        t=t
    )


# =========================================================
# CHATBOT
# =========================================================

@app.route(
    "/chatbot",
    methods=["GET", "POST"]
)
@login_required
def chatbot():

    t, lang = get_t()

    reply = None
    mode = None
    user_message = None

    if request.method == "POST":

        user_message = request.form.get(
            "message",
            ""
        )

        latest_prediction = Prediction.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Prediction.date.desc()
        ).first()

        risk_tier = (
            latest_prediction.risk_tier
            if latest_prediction
            else "Unknown"
        )

        result = get_chatbot_response(
            user_message,
            risk_tier,
            lang
        )

        reply = result["reply"]

        mode = result["mode"]

    return render_template(
        "chatbot.html",
        reply=reply,
        mode=mode,
        user_message=user_message,
        t=t
    )


# =========================================================
# DOWNLOAD HEALTH REPORT
# =========================================================

@app.route("/download-report")
@login_required
def download_report():

    latest_prediction = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.desc()
    ).first()

    if not latest_prediction:

        return (
            "No prediction found. "
            "Please make a prediction first."
        )

    t = TRANSLATIONS["en"]

    recommendations = get_recommendations(
        [
            0,
            latest_prediction.glucose,
            latest_prediction.blood_pressure,
            0,
            0,
            latest_prediction.bmi,
            0,
            30
        ],
        t
    )

    pdf_buffer = generate_health_report(
        user_name=current_user.name,
        risk_tier=latest_prediction.risk_tier,
        probability=latest_prediction.probability,
        recommendations=recommendations,
        glucose=latest_prediction.glucose,
        bmi=latest_prediction.bmi,
        bp=latest_prediction.blood_pressure,
        age=current_user.age
    )

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=(
            f"diabetes_report_"
            f"{current_user.name}.pdf"
        ),
        mimetype="application/pdf"
    )


# =========================================================
# DOCTOR LOCATOR
# =========================================================

@app.route("/doctor-locator")
@login_required
def doctor_locator():

    t, lang = get_t()

    google_maps_key = os.getenv(
        "GOOGLE_MAPS_API_KEY"
    )

    return render_template(
        "doctor_locator.html",
        google_maps_key=google_maps_key,
        t=t
    )


# =========================================================
# RISK SIMULATOR
# =========================================================

@app.route("/simulator")
@login_required
def simulator():

    t, lang = get_t()

    risk_labels = {
        "Low": t["risk_low"],
        "Medium": t["risk_medium"],
        "High": t["risk_high"]
    }

    return render_template(
        "simulator.html",
        t=t,
        risk_labels=risk_labels,
        current_lang=lang
    )


# =========================================================
# SIMULATOR API
# =========================================================

@app.route(
    "/api/simulate",
    methods=["POST"]
)
@login_required
def simulate():

    try:

        data = request.get_json()

        pregnancies = float(
            data["pregnancies"]
        )

        glucose = float(
            data["glucose"]
        )

        bp = float(
            data["bloodpressure"]
        )

        skin = float(
            data["skinthickness"]
        )

        insulin = float(
            data["insulin"]
        )

        bmi = float(
            data["bmi"]
        )

        dpf = float(
            data["dpf"]
        )

        age = float(
            data["age"]
        )

        input_data = np.array([
            [
                pregnancies,
                glucose,
                bp,
                skin,
                insulin,
                bmi,
                dpf,
                age
            ]
        ])

        input_scaled = scaler.transform(
            input_data
        )

        probability = model.predict_proba(
            input_scaled
        )[0][1]

        risk_tier = get_risk_tier(
            probability
        )

        return jsonify({

            "risk_tier": risk_tier,

            "probability": round(
                float(probability) * 100,
                2
            )

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# =========================================================
# EXERCISE VIDEOS
# =========================================================

@app.route(
    "/exercise-videos/<risk_tier>"
)
@login_required
def exercise_videos(risk_tier):

    t, lang = get_t()

    if risk_tier not in EXERCISE_VIDEOS:

        risk_tier = "Low"

    videos = EXERCISE_VIDEOS[
        risk_tier
    ]

    risk_tier_display = get_risk_tier_translated(
        risk_tier,
        t
    )

    return render_template(
        "exercise_videos.html",
        risk_tier=risk_tier,
        risk_tier_display=risk_tier_display,
        videos=videos,
        t=t
    )


# =========================================================
# BMI CALCULATOR
# =========================================================

@app.route(
    "/bmi-calculator",
    methods=["GET", "POST"]
)
@login_required
def bmi_calculator():

    t, lang = get_t()

    bmi = None
    category = None
    error = None

    if request.method == "POST":

        try:

            height = float(
                request.form["height"]
            )

            weight = float(
                request.form["weight"]
            )

            if height <= 0 or weight <= 0:

                error = t["bmi_invalid"]

            else:

                height_m = height / 100

                bmi = round(
                    weight /
                    (
                        height_m *
                        height_m
                    ),
                    2
                )

                # =========================================
                # BMI CATEGORY
                # =========================================

                if bmi < 18.5:

                    category = t["bmi_underweight"]

                elif bmi < 25:

                    category = t["bmi_normal"]

                elif bmi < 30:

                    category = t["bmi_overweight"]

                else:

                    category = t["bmi_obese"]

        except (
            ValueError,
            TypeError
        ):

            error = t["bmi_invalid_numbers"]

    return render_template(
        "bmi_calculator.html",
        bmi=bmi,
        category=category,
        error=error,
        t=t,
        current_lang=lang
    )


# =========================================================
# MEDICATION
# =========================================================

@app.route("/medication")
@login_required
def medication():

    t, lang = get_t()

    latest_prediction = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.desc()
    ).first()

    if latest_prediction:

        risk_tier = (
            latest_prediction.risk_tier
        )

        probability = (
            latest_prediction.probability
        )

    else:

        risk_tier = "Low"

        probability = 0

    return render_template(
        "medication.html",
        t=t,
        risk_tier=risk_tier,
        probability=probability
    )


# =========================================================
# APPOINTMENTS
# =========================================================

@app.route(
    "/appointments",
    methods=["GET", "POST"]
)
@login_required
def appointments():

    t, lang = get_t()

    latest_prediction = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.desc()
    ).first()

    if latest_prediction:

        risk_tier = latest_prediction.risk_tier

    else:

        risk_tier = "Low"

    if risk_tier not in [
        "Low",
        "Medium",
        "High"
    ]:

        risk_tier = "Low"

    # -----------------------------------------------------
    # POST = BOOK APPOINTMENT
    # -----------------------------------------------------

    if request.method == "POST":

        doctor = request.form.get(
            "doctor",
            ""
        ).strip()

        appointment_date = request.form.get(
            "appointment_date",
            ""
        ).strip()

        appointment_time = request.form.get(
            "appointment_time",
            ""
        ).strip()

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        if not doctor:

            flash(
                t.get(
                    "select_doctor",
                    "Please select a doctor."
                )
            )

            return redirect(
                url_for("appointments")
            )

        if not appointment_date:

            flash(
                t.get(
                    "appointment_date",
                    "Please select an appointment date."
                )
            )

            return redirect(
                url_for("appointments")
            )

        if not appointment_time:

            flash(
                t.get(
                    "appointment_time",
                    "Please select an appointment time."
                )
            )

            return redirect(
                url_for("appointments")
            )

        # -------------------------------------------------
        # DATE VALIDATION
        # -------------------------------------------------

        try:

            selected_date = datetime.strptime(
                appointment_date,
                "%Y-%m-%d"
            ).date()

            today = datetime.now().date()

            if selected_date < today:

                flash(
                    "Appointment date cannot be in the past."
                )

                return redirect(
                    url_for("appointments")
                )

        except ValueError:

            flash(
                "Invalid appointment date."
            )

            return redirect(
                url_for("appointments")
            )

        # -------------------------------------------------
        # TIME VALIDATION
        # -------------------------------------------------

        try:

            selected_time = datetime.strptime(
                appointment_time,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid appointment time."
            )

            return redirect(
                url_for("appointments")
            )

        # -------------------------------------------------
        # IF TODAY, TIME MUST BE FUTURE
        # -------------------------------------------------

        if selected_date == today:

            current_time = datetime.now().time()

            if selected_time <= current_time:

                flash(
                    "Please select a future appointment time."
                )

                return redirect(
                    url_for("appointments")
                )

        # -------------------------------------------------
        # GET APPOINTMENTS
        # -------------------------------------------------

        appointments_list = session.get(
            "appointments",
            []
        )

        if not isinstance(
            appointments_list,
            list
        ):

            appointments_list = []

        # -------------------------------------------------
        # CREATE APPOINTMENT
        # -------------------------------------------------

        new_appointment = {

            "doctor": doctor,

            "date": appointment_date,

            "time": appointment_time,

            "reason": reason,

            "patient": current_user.name

        }

        appointments_list.append(
            new_appointment
        )

        session["appointments"] = (
            appointments_list
        )

        session.modified = True

        flash(
            t.get(
                "appointment_success",
                "Appointment booked successfully!"
            )
        )

        return redirect(
            url_for("appointments")
        )

    # =====================================================
    # GET = DISPLAY APPOINTMENTS
    # =====================================================

    appointments_list = session.get(
        "appointments",
        []
    )

    if not isinstance(
        appointments_list,
        list
    ):

        appointments_list = []

    return render_template(
        "appointments.html",

        t=t,

        appointments=appointments_list,

        risk_tier=risk_tier,

        current_lang=lang
    )


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

@app.route(
    "/cancel-appointment/<int:index>",
    methods=["POST"]
)
@login_required
def cancel_appointment(index):

    appointments_list = session.get(
        "appointments",
        []
    )

    if not isinstance(
        appointments_list,
        list
    ):

        appointments_list = []

    if 0 <= index < len(
        appointments_list
    ):

        appointments_list.pop(
            index
        )

        session["appointments"] = (
            appointments_list
        )

        session.modified = True

        flash(
            "Appointment cancelled successfully."
        )

    else:

        flash(
            "Appointment not found."
        )

    return redirect(
        url_for("appointments")
    )


# =========================================================
# PROGRESS
# =========================================================

@app.route("/progress")
@login_required
def progress():

    t, lang = get_t()

    predictions = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.asc()
    ).all()

    dates = [
        p.date.strftime("%d-%b-%Y")
        for p in predictions
    ]

    glucose_values = [
        p.glucose
        for p in predictions
    ]

    bmi_values = [
        p.bmi
        for p in predictions
    ]

    risk_probabilities = [
        p.probability
        for p in predictions
    ]

    risk_tiers = [
        get_risk_tier_translated(
            p.risk_tier,
            t
        )
        for p in predictions
    ]

    return render_template(
        "progress.html",
        t=t,
        predictions=predictions,
        dates=dates,
        glucose_values=glucose_values,
        bmi_values=bmi_values,
        risk_probabilities=risk_probabilities,
        risk_tiers=risk_tiers
    )


# =========================================================
# MONTHLY REPORT
# =========================================================

@app.route("/monthly-report")
@login_required
def monthly_report():

    t, lang = get_t()

    predictions = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.desc()
    ).all()

    total_predictions = len(
        predictions
    )

    if predictions:

        glucose_data = [
            p.glucose
            for p in predictions
            if p.glucose is not None
        ]

        bmi_data = [
            p.bmi
            for p in predictions
            if p.bmi is not None
        ]

        if glucose_data:

            average_glucose = round(
                sum(glucose_data) /
                len(glucose_data),
                2
            )

        else:

            average_glucose = 0

        if bmi_data:

            average_bmi = round(
                sum(bmi_data) /
                len(bmi_data),
                2
            )

        else:

            average_bmi = 0

        latest_prediction = predictions[0]

        latest_risk = (
            latest_prediction.risk_tier
        )

        latest_probability = (
            latest_prediction.probability
        )

    else:

        average_glucose = 0

        average_bmi = 0

        latest_risk = "No Data"

        latest_probability = 0

    return render_template(
        "monthly_report.html",
        t=t,
        predictions=predictions,
        total_predictions=total_predictions,
        average_glucose=average_glucose,
        average_bmi=average_bmi,
        latest_risk=latest_risk,
        latest_probability=latest_probability
    )


# =========================================================
# CREATE DATABASE AND RUN APP
# =========================================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(
        debug=True
    )
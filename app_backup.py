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

import joblib
import numpy as np
import pandas as pd
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

MODEL_PATH = "model/diabetes_model.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# =========================================================
# LOAD MODEL INFORMATION
# =========================================================

MODEL_INFO_PATH = "model/model_info.pkl"

if os.path.exists(MODEL_INFO_PATH):
    model_info = joblib.load(MODEL_INFO_PATH)
else:
    model_info = {}


# =========================================================
# TRANSLATION
# =========================================================

def get_t():

    lang = session.get("lang", "en")

    if lang not in TRANSLATIONS:
        lang = "en"

    return TRANSLATIONS[lang], lang


# =========================================================
# RISK FUNCTIONS
# =========================================================

def get_risk_tier(probability):

    # probability MUST be 0.0 - 1.0

    if probability < 0.33:
        return "Low"

    elif probability < 0.66:
        return "Medium"

    else:
        return "High"


def get_risk_tier_translated(risk_tier, t):

    mapping = {
        "Low": t.get("risk_low", "Low"),
        "Medium": t.get("risk_medium", "Medium"),
        "High": t.get("risk_high", "High")
    }

    return mapping.get(risk_tier, risk_tier)


# =========================================================
# RECOMMENDATIONS
# =========================================================

def get_recommendations(data, t):

    tips = []

    glucose = data.get("blood_glucose_level", 0)
    bmi = data.get("bmi", 0)
    hba1c = data.get("hbA1c_level", 0)
    age = data.get("age", 0)
    hypertension = data.get("hypertension", 0)
    heart_disease = data.get("heart_disease", 0)

    # GLUCOSE

    if glucose >= 126:

        tips.append(
            t.get(
                "tip_glucose",
                "Your blood glucose level is high. Please consider consulting a healthcare professional."
            )
        )

    elif glucose >= 100:

        tips.append(
            "Your blood glucose level is above the normal range. Maintain a healthy diet and regular physical activity."
        )

    # BMI

    if bmi >= 30:

        tips.append(
            "Your BMI is in the obese range. A balanced diet and regular physical activity may help."
        )

    elif bmi >= 25:

        tips.append(
            t.get(
                "tip_bmi",
                "Your BMI is above the normal range. Regular physical activity and a balanced diet may help."
            )
        )

    # HbA1c

    if hba1c >= 6.5:

        tips.append(
            "Your HbA1c level is elevated. Please consult a healthcare professional for proper evaluation."
        )

    elif hba1c >= 5.7:

        tips.append(
            "Your HbA1c level is in an elevated range. Regular monitoring may be helpful."
        )

    # AGE

    if age >= 45:

        tips.append(
            t.get(
                "tip_age",
                "Regular diabetes screening is recommended, especially with increasing age."
            )
        )

    # HYPERTENSION

    if hypertension == 1:

        tips.append(
            "Hypertension is present. Regular blood pressure monitoring is recommended."
        )

    # HEART DISEASE

    if heart_disease == 1:

        tips.append(
            "Heart disease is reported. Please follow your healthcare professional's advice."
        )

    # DEFAULT

    if not tips:

        tips.append(
            t.get(
                "tip_healthy",
                "Continue maintaining a healthy lifestyle with balanced nutrition and regular physical activity."
            )
        )

    return tips


# =========================================================
# BMI
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


def get_bmi_category_translated(category, t):

    mapping = {
        "Underweight": t.get("bmi_underweight", "Underweight"),
        "Normal Weight": t.get("bmi_normal", "Normal Weight"),
        "Overweight": t.get("bmi_overweight", "Overweight"),
        "Obese": t.get("bmi_obese", "Obese")
    }

    return mapping.get(category, category)


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

    lang = session.get("lang", "en")

    s = str(value)

    if lang == "kn":
        return s.translate(KANNADA_DIGITS)

    elif lang == "hi":
        return s.translate(HINDI_DIGITS)

    return s


# =========================================================
# DATE FORMAT
# =========================================================

def format_date_localized(dt, t, lang):

    day = str(dt.day).zfill(2)

    month_key = f"month_{dt.month:02d}"

    month_name = t.get(
        month_key,
        dt.strftime("%B")
    )

    year = str(dt.year)

    time_part = dt.strftime("%H:%M")

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
# LANGUAGE
# =========================================================

@app.route("/set-language/<lang_code>")
def set_language(lang_code):

    if lang_code in TRANSLATIONS:

        session["lang"] = lang_code

    return redirect(
        request.referrer or url_for("home")
    )


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        age = request.form.get(
            "age", ""
        )

        gender = request.form.get(
            "gender", ""
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

        db.session.add(new_user)

        db.session.commit()

        flash(
            "Account created successfully! Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template("signup.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip()

        password = request.form.get(
            "password", ""
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

        flash(
            "Invalid email or password."
        )

        return redirect(
            url_for("login")
        )

    return render_template("login.html")


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

    latest_prediction = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.desc()
    ).first()

    risk_probability = None
    risk_tier = None
    risk_tier_display = None

    overview_glucose = None
    overview_bmi = None

    overview_age = current_user.age or None

    overview_hypertension = None
    overview_heart_disease = None
    overview_hba1c = None

    if latest_prediction:

        risk_probability = float(
            latest_prediction.probability
        )

        risk_tier = latest_prediction.risk_tier

        risk_tier_display = get_risk_tier_translated(
            risk_tier,
            t
        )

        overview_glucose = latest_prediction.glucose

        overview_bmi = latest_prediction.bmi

    return render_template(
        "index.html",

        t=t,

        current_lang=lang,

        latest_prediction=latest_prediction,

        risk_probability=risk_probability,

        risk_tier=risk_tier,

        risk_tier_display=risk_tier_display,

        overview_glucose=overview_glucose,

        overview_bmi=overview_bmi,

        overview_age=overview_age,

        overview_hypertension=overview_hypertension,

        overview_heart_disease=overview_heart_disease,

        overview_hba1c=overview_hba1c
    )


# =========================================================
# AI RISK OVERVIEW
# =========================================================

@app.route("/risk-overview")
@login_required
def risk_overview():

    t, lang = get_t()

    latest_prediction = Prediction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prediction.date.desc()
    ).first()

    # -------------------------------------------------
    # NO PREDICTION
    # -------------------------------------------------

    if not latest_prediction:

        return render_template(

            "risk_overview.html",

            t=t,

            current_lang=lang,

            has_prediction=False,

            risk_probability=0,

            risk_tier="Low",

            risk_tier_display=
                t.get(
                    "risk_low",
                    "Low"
                ),

            glucose=None,

            bmi=None,

            age=current_user.age or None

        )

    # -------------------------------------------------
    # GET SAVED PROBABILITY
    # -------------------------------------------------

    risk_probability = float(
        latest_prediction.probability or 0
    )

    # -------------------------------------------------
    # IMPORTANT
    #
    # Database stores percentage.
    #
    # Example:
    # 0.82 model probability
    # becomes
    # 82.0 database value
    #
    # So DO NOT multiply by 100 here.
    # -------------------------------------------------

    risk_probability = round(
        risk_probability,
        2
    )

    risk_tier = (
        latest_prediction.risk_tier
    )

    risk_tier_display = (
        get_risk_tier_translated(
            risk_tier,
            t
        )
    )

    print("\n====================================")
    print("RISK OVERVIEW")
    print("====================================")

    print(
        "Database probability:",
        latest_prediction.probability
    )

    print(
        "Displayed probability:",
        risk_probability
    )

    print(
        "Risk tier:",
        risk_tier
    )

    # -------------------------------------------------
    # RETURN PAGE
    # -------------------------------------------------

    return render_template(

        "risk_overview.html",

        t=t,

        current_lang=lang,

        has_prediction=True,

        latest_prediction=
            latest_prediction,

        risk_probability=
            risk_probability,

        risk_tier=
            risk_tier,

        risk_tier_display=
            risk_tier_display,

        glucose=
            latest_prediction.glucose,

        bmi=
            latest_prediction.bmi,

        age=
            current_user.age or None

    )
    # IMPORTANT:
    # Database stores probability as percentage.
    # Example:
    # 0.73 model probability
    # 73.0 database/display probability

    risk_probability = float(
        latest_prediction.probability
    )

    risk_tier = latest_prediction.risk_tier

    risk_tier_display = get_risk_tier_translated(
        risk_tier,
        t
    )

    return render_template(
        "risk_overview.html",

        t=t,

        current_lang=lang,

        has_prediction=True,

        latest_prediction=latest_prediction,

        risk_probability=risk_probability,

        risk_tier=risk_tier,

        risk_tier_display=risk_tier_display,

        glucose=latest_prediction.glucose,

        bmi=latest_prediction.bmi,

        age=current_user.age or None
    )


# =========================================================
# CREATE PREDICTION DATAFRAME
# =========================================================

def create_prediction_dataframe(
    year,
    gender,
    age,
    location,
    race,
    hypertension,
    heart_disease,
    smoking_history,
    bmi,
    hbA1c_level,
    blood_glucose_level
):

    return pd.DataFrame({

        "year": [year],

        "gender": [gender],

        "age": [age],

        "location": [location],

        "race:AfricanAmerican": [
            1 if race == "AfricanAmerican" else 0
        ],

        "race:Asian": [
            1 if race == "Asian" else 0
        ],

        "race:Caucasian": [
            1 if race == "Caucasian" else 0
        ],

        "race:Hispanic": [
            1 if race == "Hispanic" else 0
        ],

        "race:Other": [
            1 if race == "Other" else 0
        ],

        "hypertension": [hypertension],

        "heart_disease": [heart_disease],

        "smoking_history": [smoking_history],

        "bmi": [bmi],

        "hbA1c_level": [hbA1c_level],

        "blood_glucose_level": [
            blood_glucose_level
        ]
    })


# =========================================================
# SHAP
# =========================================================

def generate_shap_contributions(input_data, t):

    try:

        import shap

        # Pipeline model

        if hasattr(model, "named_steps"):

            steps = model.named_steps

            preprocessor = None
            classifier = None

            for name, step in steps.items():

                if (
                    hasattr(step, "transform")
                    and not hasattr(step, "predict_proba")
                ):
                    preprocessor = step

                if hasattr(
                    step,
                    "predict_proba"
                ):
                    classifier = step

            if classifier is None:
                classifier = model

            if preprocessor is not None:

                transformed_data = (
                    preprocessor.transform(
                        input_data
                    )
                )

            else:

                transformed_data = input_data

            explainer = shap.TreeExplainer(
                classifier
            )

            shap_values = explainer.shap_values(
                transformed_data
            )

            if isinstance(shap_values, list):

                values = np.asarray(
                    shap_values[-1]
                )[0]

            else:

                shap_array = np.asarray(
                    shap_values
                )

                if shap_array.ndim == 3:

                    values = shap_array[
                        0, :, -1
                    ]

                elif shap_array.ndim == 2:

                    values = shap_array[0]

                else:

                    values = shap_array.flatten()

            try:

                if preprocessor is not None:

                    feature_names = list(
                        preprocessor.get_feature_names_out()
                    )

                else:

                    feature_names = list(
                        input_data.columns
                    )

            except Exception:

                feature_names = list(
                    input_data.columns
                )

            count = min(
                len(values),
                len(feature_names)
            )

            values = values[:count]

            feature_names = feature_names[:count]

            total_abs = float(
                np.sum(
                    np.abs(values)
                )
            )

            if total_abs == 0:
                total_abs = 1.0

            label_mapping = {

                "age": t.get(
                    "age",
                    "Age"
                ),

                "bmi": t.get(
                    "bmi",
                    "BMI"
                ),

                "hbA1c_level":
                    "HbA1c Level",

                "blood_glucose_level":
                    "Blood Glucose Level",

                "hypertension":
                    "Hypertension",

                "heart_disease":
                    "Heart Disease",

                "year":
                    "Year",

                "gender":
                    "Gender",

                "location":
                    "Location",

                "smoking_history":
                    "Smoking History",

                "race:AfricanAmerican":
                    "African American",

                "race:Asian":
                    "Asian",

                "race:Caucasian":
                    "Caucasian",

                "race:Hispanic":
                    "Hispanic",

                "race:Other":
                    "Other"
            }

            contributions = []

            for i in range(count):

                value = float(
                    values[i]
                )

                percent = round(
                    (
                        abs(value)
                        /
                        total_abs
                    ) * 100,
                    1
                )

                label = str(
                    feature_names[i]
                )

                label = label.replace(
                    "num__",
                    ""
                )

                label = label.replace(
                    "cat__",
                    ""
                )

                if label in label_mapping:

                    display_label = (
                        label_mapping[label]
                    )

                elif "gender_" in label:

                    display_label = (
                        "Gender: "
                        +
                        label.replace(
                            "gender_",
                            ""
                        )
                    )

                elif "location_" in label:

                    display_label = (
                        "Location: "
                        +
                        label.replace(
                            "location_",
                            ""
                        )
                    )

                elif "smoking_history_" in label:

                    display_label = (
                        "Smoking: "
                        +
                        label.replace(
                            "smoking_history_",
                            ""
                        )
                    )

                else:

                    display_label = label

                contributions.append({

                    "label":
                        display_label,

                    "value":
                        value,

                    "percent":
                        percent
                })

            contributions.sort(
                key=lambda x: abs(
                    x["value"]
                ),
                reverse=True
            )

            return contributions[:10]

        # Plain model

        explainer = shap.TreeExplainer(model)

        shap_values = explainer.shap_values(
            input_data
        )

        if isinstance(
            shap_values,
            list
        ):

            values = np.asarray(
                shap_values[-1]
            )[0]

        else:

            shap_array = np.asarray(
                shap_values
            )

            if shap_array.ndim == 3:

                values = shap_array[
                    0, :, -1
                ]

            elif shap_array.ndim == 2:

                values = shap_array[0]

            else:

                values = shap_array.flatten()

        feature_names = list(
            input_data.columns
        )

        total_abs = float(
            np.sum(
                np.abs(values)
            )
        )

        if total_abs == 0:
            total_abs = 1.0

        contributions = []

        for i, value in enumerate(values):

            if i >= len(feature_names):
                break

            value = float(value)

            contributions.append({

                "label":
                    feature_names[i],

                "value":
                    value,

                "percent":
                    round(
                        (
                            abs(value)
                            /
                            total_abs
                        ) * 100,
                        1
                    )
            })

        contributions.sort(
            key=lambda x: abs(
                x["value"]
            ),
            reverse=True
        )

        return contributions[:10]

    except Exception as e:

        print(
            "SHAP ERROR:",
            str(e)
        )

        return []


# =========================================================
# DIABETES PREDICTION
# =========================================================

@app.route("/predict", methods=["POST"])
@login_required
def predict():

    try:

        # -------------------------------------------------
        # GET INPUT VALUES
        # -------------------------------------------------

        year = int(
            request.form.get(
                "year",
                datetime.now().year
            )
        )

        gender = request.form.get(
            "gender",
            "Female"
        )

        age = float(
            request.form.get(
                "age",
                current_user.age or 30
            )
        )

        location = request.form.get(
            "location",
            "Other"
        )

        race = request.form.get(
            "race",
            "Other"
        )

        hypertension = int(
            request.form.get(
                "hypertension",
                0
            )
        )

        heart_disease = int(
            request.form.get(
                "heart_disease",
                0
            )
        )

        smoking_history = request.form.get(
            "smoking_history",
            "never"
        )

        bmi = float(
            request.form.get(
                "bmi",
                25
            )
        )

        hbA1c_level = float(
            request.form.get(
                "hbA1c_level",
                5.5
            )
        )

        blood_glucose_level = float(
            request.form.get(
                "blood_glucose_level",
                100
            )
        )

        # -------------------------------------------------
        # CREATE DATAFRAME
        # -------------------------------------------------

        input_data = create_prediction_dataframe(

            year=year,

            gender=gender,

            age=age,

            location=location,

            race=race,

            hypertension=hypertension,

            heart_disease=heart_disease,

            smoking_history=smoking_history,

            bmi=bmi,

            hbA1c_level=hbA1c_level,

            blood_glucose_level=blood_glucose_level

        )

        print("\n====================================")
        print("PATIENT INPUT")
        print("====================================")
        print(input_data)

        # -------------------------------------------------
        # AI MODEL PREDICTION
        # -------------------------------------------------

        prediction_result = model.predict_proba(
            input_data
        )

        print("\n====================================")
        print("MODEL PREDICTION")
        print("====================================")

        print(
            "Class 0 probability:",
            prediction_result[0][0]
        )

        print(
            "Class 1 probability:",
            prediction_result[0][1]
        )

        # -------------------------------------------------
        # DIABETES PROBABILITY
        # -------------------------------------------------

        probability = float(
            prediction_result[0][1]
        )

        probability_percent = round(
            probability * 100,
            2
        )

        print(
            "DIABETES PROBABILITY:",
            probability
        )

        print(
            "DIABETES PROBABILITY (%):",
            probability_percent
        )

        # -------------------------------------------------
        # SAFETY CHECK
        # -------------------------------------------------

        if probability_percent < 0:
            probability_percent = 0

        if probability_percent > 100:
            probability_percent = 100

        # -------------------------------------------------
        # RISK TIER
        # -------------------------------------------------

        risk_tier = get_risk_tier(
            probability
        )

        print(
            "RISK TIER:",
            risk_tier
        )

        # -------------------------------------------------
        # TRANSLATION
        # -------------------------------------------------

        t, lang = get_t()

        risk_tier_display = (
            get_risk_tier_translated(
                risk_tier,
                t
            )
        )

        # -------------------------------------------------
        # RECOMMENDATIONS
        # -------------------------------------------------

        recommendations = get_recommendations(

            {
                "blood_glucose_level":
                    blood_glucose_level,

                "bmi":
                    bmi,

                "hbA1c_level":
                    hbA1c_level,

                "age":
                    age,

                "hypertension":
                    hypertension,

                "heart_disease":
                    heart_disease
            },

            t
        )

        # -------------------------------------------------
        # SAVE CORRECT VALUE TO DATABASE
        #
        # IMPORTANT:
        # probability column stores percentage.
        # Example:
        # model = 0.72
        # database = 72.0
        # -------------------------------------------------

        new_prediction = Prediction(

            user_id=current_user.id,

            glucose=blood_glucose_level,

            bmi=bmi,

            blood_pressure=0,

            risk_tier=risk_tier,

            probability=probability_percent

        )

        db.session.add(
            new_prediction
        )

        db.session.commit()

        print("\n====================================")
        print("DATABASE SAVED")
        print("====================================")

        print(
            "Saved probability:",
            new_prediction.probability
        )

        print(
            "Saved risk:",
            new_prediction.risk_tier
        )

        # -------------------------------------------------
        # SHAP EXPLANATION
        # -------------------------------------------------

        shap_contributions = (
            generate_shap_contributions(
                input_data,
                t
            )
        )

        print("\n====================================")
        print("SHAP CONTRIBUTIONS")
        print("====================================")

        print(
            shap_contributions
        )

        # -------------------------------------------------
        # RESULT PAGE
        # -------------------------------------------------

        return render_template(

            "result.html",

            risk_tier=risk_tier,

            risk_tier_display=
                risk_tier_display,

            probability=
                probability_percent,

            recommendations=
                recommendations,

            shap_contributions=
                shap_contributions,

            t=t

        )

    except Exception as e:

        print(
            "\n===================================="
        )

        print(
            "PREDICTION ERROR:"
        )

        print(
            str(e)
        )

        print(
            "===================================="
        )

        return (

            f"Prediction Error: {str(e)}"

        ), 400


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

        risk_probabilities=
            risk_probabilities,

        risk_tiers_translated=
            risk_tiers_translated,

        table_dates=table_dates,

        t=t
    )


# =========================================================
# MEAL PLAN
# =========================================================

@app.route("/meal-plan/<risk_tier>")
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

            "day":
                t[day_key],

            "breakfast":
                translate_dish(
                    breakfast_dish,
                    lang
                ),

            "lunch":
                translate_dish(
                    lunch_dish,
                    lang
                ),

            "dinner":
                translate_dish(
                    dinner_dish,
                    lang
                )
        })

    risk_tier_display = (
        get_risk_tier_translated(
            risk_tier,
            t
        )
    )

    return render_template(

        "meal_plan.html",

        risk_tier=risk_tier,

        risk_tier_display=
            risk_tier_display,

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
# DOWNLOAD REPORT
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

        {

            "blood_glucose_level":
                latest_prediction.glucose,

            "bmi":
                latest_prediction.bmi,

            "hbA1c_level":
                0,

            "age":
                float(
                    current_user.age or 30
                ),

            "hypertension":
                0,

            "heart_disease":
                0

        },

        t
    )

    pdf_buffer = generate_health_report(

        user_name=current_user.name,

        risk_tier=
            latest_prediction.risk_tier,

        probability=
            latest_prediction.probability,

        recommendations=
            recommendations,

        glucose=
            latest_prediction.glucose,

        bmi=
            latest_prediction.bmi,

        bp=
            latest_prediction.blood_pressure,

        age=
            current_user.age
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

        google_maps_key=
            google_maps_key,

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

        "Low":
            t["risk_low"],

        "Medium":
            t["risk_medium"],

        "High":
            t["risk_high"]
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

        if not data:
            return jsonify({
                "error": "No input data received."
            }), 400

        input_data = pd.DataFrame([{

            "year":
                int(
                    data.get(
                        "year",
                        datetime.now().year
                    )
                ),

            "gender":
                data.get(
                    "gender",
                    "Female"
                ),

            "age":
                float(
                    data.get(
                        "age",
                        30
                    )
                ),

            "location":
                data.get(
                    "location",
                    "Other"
                ),

            "race:AfricanAmerican":
                int(
                    data.get(
                        "race_african",
                        0
                    )
                ),

            "race:Asian":
                int(
                    data.get(
                        "race_asian",
                        0
                    )
                ),

            "race:Caucasian":
                int(
                    data.get(
                        "race_caucasian",
                        0
                    )
                ),

            "race:Hispanic":
                int(
                    data.get(
                        "race_hispanic",
                        0
                    )
                ),

            "race:Other":
                int(
                    data.get(
                        "race_other",
                        0
                    )
                ),

            "hypertension":
                int(
                    data.get(
                        "hypertension",
                        0
                    )
                ),

            "heart_disease":
                int(
                    data.get(
                        "heart_disease",
                        0
                    )
                ),

            "smoking_history":
                data.get(
                    "smoking_history",
                    "never"
                ),

            "bmi":
                float(
                    data.get(
                        "bmi",
                        25
                    )
                ),

            "hbA1c_level":
                float(
                    data.get(
                        "hbA1c_level",
                        5.5
                    )
                ),

            "blood_glucose_level":
                float(
                    data.get(
                        "blood_glucose_level",
                        100
                    )
                )

        }])

        print("\n==============================")
        print("SIMULATOR INPUT")
        print("==============================")

        print(input_data)

        # -------------------------------------------------
        # AI PREDICTION
        # -------------------------------------------------

        prediction_result = model.predict_proba(
            input_data
        )

        print("\n==============================")
        print("SIMULATOR MODEL PROBABILITIES")
        print("==============================")

        print(
            "Class 0 probability:",
            prediction_result[0][0]
        )

        print(
            "Class 1 probability:",
            prediction_result[0][1]
        )

        # RAW probability
        probability = float(
            prediction_result[0][1]
        )

        # DISPLAY percentage
        probability_percent = round(
            probability * 100,
            2
        )

        print(
            "RAW PROBABILITY:",
            probability
        )

        print(
            "PERCENTAGE:",
            probability_percent
        )

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        risk_tier = get_risk_tier(
            probability
        )

        print(
            "RISK TIER:",
            risk_tier
        )

        # -------------------------------------------------
        # RETURN JSON
        # -------------------------------------------------

        return jsonify({

            "risk_tier":
                risk_tier,

            "probability":
                probability_percent

        })

    except Exception as e:

        print(
            "SIMULATOR ERROR:",
            str(e)
        )

        return jsonify({

            "error":
                str(e)

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

    videos = EXERCISE_VIDEOS[risk_tier]

    risk_tier_display = (
        get_risk_tier_translated(
            risk_tier,
            t
        )
    )

    return render_template(

        "exercise_videos.html",

        risk_tier=risk_tier,

        risk_tier_display=
            risk_tier_display,

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

                error = t[
                    "bmi_invalid"
                ]

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

                if bmi < 18.5:

                    category = t[
                        "bmi_underweight"
                    ]

                elif bmi < 25:

                    category = t[
                        "bmi_normal"
                    ]

                elif bmi < 30:

                    category = t[
                        "bmi_overweight"
                    ]

                else:

                    category = t[
                        "bmi_obese"
                    ]

        except (
            ValueError,
            TypeError
        ):

            error = t[
                "bmi_invalid_numbers"
            ]

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

        probability = float(
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

        risk_tier = (
            latest_prediction.risk_tier
        )

    else:

        risk_tier = "Low"

    if risk_tier not in [
        "Low",
        "Medium",
        "High"
    ]:

        risk_tier = "Low"

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

        if selected_date == today:

            current_time = datetime.now().time()

            if selected_time <= current_time:

                flash(
                    "Please select a future appointment time."
                )

                return redirect(
                    url_for("appointments")
                )

        appointments_list = session.get(
            "appointments",
            []
        )

        if not isinstance(
            appointments_list,
            list
        ):

            appointments_list = []

        new_appointment = {

            "doctor":
                doctor,

            "date":
                appointment_date,

            "time":
                appointment_time,

            "reason":
                reason,

            "patient":
                current_user.name
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

        appointments=
            appointments_list,

        risk_tier=
            risk_tier,

        current_lang=
            lang
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

        appointments_list.pop(index)

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

        glucose_values=
            glucose_values,

        bmi_values=
            bmi_values,

        risk_probabilities=
            risk_probabilities,

        risk_tiers=
            risk_tiers
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
                sum(glucose_data)
                /
                len(glucose_data),
                2
            )

        else:

            average_glucose = 0

        if bmi_data:

            average_bmi = round(
                sum(bmi_data)
                /
                len(bmi_data),
                2
            )

        else:

            average_bmi = 0

        latest_prediction = predictions[0]

        latest_risk = (
            latest_prediction.risk_tier
        )

        latest_probability = float(
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

        total_predictions=
            total_predictions,

        average_glucose=
            average_glucose,

        average_bmi=
            average_bmi,

        latest_risk=
            latest_risk,

        latest_probability=
            latest_probability
    )


# =========================================================
# CREATE DATABASE AND RUN
# =========================================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(
        debug=True
    )
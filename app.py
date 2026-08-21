# =========================================================
# MEDIHIVE AI - COMPLETE FLASK APPLICATION
# =========================================================

import os
import random
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

from dotenv import load_dotenv

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

from models import (
    db,
    User,
    Prediction,
    Medication,
    Appointment,
    Notification
)

from meal_data import MEAL_PLANS
from meal_translations import translate_dish
from chatbot_logic import get_chatbot_response
from pdf_generator import generate_health_report
from translations import TRANSLATIONS
from exercise_data import EXERCISE_VIDEOS


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-to-a-random-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///database.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# =========================================================
# LOGIN MANAGER
# =========================================================

login_manager = LoginManager()

login_manager.login_view = "login"

login_manager.login_message = (
    "Please login to access this page."
)

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):

    try:
        return User.query.get(int(user_id))

    except Exception:
        return None


# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

MODEL_PATH = os.path.join(
    "model",
    "diabetes_model.pkl"
)

if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# =========================================================
# LOAD MODEL INFORMATION
# =========================================================

MODEL_INFO_PATH = os.path.join(
    "model",
    "model_info.pkl"
)

if os.path.exists(MODEL_INFO_PATH):

    try:
        model_info = joblib.load(
            MODEL_INFO_PATH
        )

    except Exception:

        model_info = {}

else:

    model_info = {}


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

    """
    probability is expected as decimal:
    0.00 - 1.00
    """

    probability = float(
        probability or 0
    )

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

        "Low": t.get(
            "risk_low",
            "Low"
        ),

        "Medium": t.get(
            "risk_medium",
            "Medium"
        ),

        "High": t.get(
            "risk_high",
            "High"
        )

    }

    return mapping.get(
        risk_tier,
        risk_tier
    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

def get_recommendations(
    data,
    t
):

    tips = []

    glucose = float(
        data.get(
            "blood_glucose_level",
            0
        ) or 0
    )

    bmi = float(
        data.get(
            "bmi",
            0
        ) or 0
    )

    hba1c = float(
        data.get(
            "hbA1c_level",
            0
        ) or 0
    )

    age = float(
        data.get(
            "age",
            0
        ) or 0
    )

    hypertension = int(
        data.get(
            "hypertension",
            0
        ) or 0
    )

    heart_disease = int(
        data.get(
            "heart_disease",
            0
        ) or 0
    )

    # -----------------------------------------------------
    # GLUCOSE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # BMI
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # HbA1c
    # -----------------------------------------------------

    if hba1c >= 6.5:

        tips.append(
            "Your HbA1c level is elevated. Please consult a healthcare professional for proper evaluation."
        )

    elif hba1c >= 5.7:

        tips.append(
            "Your HbA1c level is in an elevated range. Regular monitoring may be helpful."
        )

    # -----------------------------------------------------
    # AGE
    # -----------------------------------------------------

    if age >= 45:

        tips.append(
            t.get(
                "tip_age",
                "Regular diabetes screening is recommended, especially with increasing age."
            )
        )

    # -----------------------------------------------------
    # HYPERTENSION
    # -----------------------------------------------------

    if hypertension == 1:

        tips.append(
            "Hypertension is present. Regular blood pressure monitoring is recommended."
        )

    # -----------------------------------------------------
    # HEART DISEASE
    # -----------------------------------------------------

    if heart_disease == 1:

        tips.append(
            "Heart disease is reported. Please follow your healthcare professional's advice."
        )

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    if not tips:

        tips.append(
            t.get(
                "tip_healthy",
                "Continue maintaining a healthy lifestyle with balanced nutrition and regular physical activity."
            )
        )

    return tips


# =========================================================
# BMI FUNCTIONS
# =========================================================

def get_bmi_category(bmi):

    bmi = float(bmi)

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
            t.get(
                "bmi_underweight",
                "Underweight"
            ),

        "Normal Weight":
            t.get(
                "bmi_normal",
                "Normal Weight"
            ),

        "Overweight":
            t.get(
                "bmi_overweight",
                "Overweight"
            ),

        "Obese":
            t.get(
                "bmi_obese",
                "Obese"
            )

    }

    return mapping.get(
        category,
        category
    )


# =========================================================
# LOCAL DIGITS
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

    value = str(value)

    if lang == "kn":

        return value.translate(
            KANNADA_DIGITS
        )

    if lang == "hi":

        return value.translate(
            HINDI_DIGITS
        )

    return value


# =========================================================
# DATE FORMAT
# =========================================================

def format_date_localized(
    dt,
    t,
    lang
):

    if not dt:

        return ""

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
# LANGUAGE
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

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name or not email or not password:

            flash(
                "Please fill all required fields."
            )

            return redirect(
                url_for("signup")
            )

        # -------------------------------------------------
        # EXISTING USER
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

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

            login_user(
                user
            )

            return redirect(
                url_for("home")
            )

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

    latest_prediction = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .first()
    )

    risk_probability = None
    risk_tier = None
    risk_tier_display = None

    overview_glucose = None
    overview_bmi = None

    overview_age = (
        current_user.age or None
    )

    overview_hypertension = None
    overview_heart_disease = None
    overview_hba1c = None

    if latest_prediction:

        risk_probability = float(
            latest_prediction.probability or 0
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

        overview_glucose = (
            latest_prediction.glucose
        )

        overview_bmi = (
            latest_prediction.bmi
        )

        if hasattr(
            latest_prediction,
            "hypertension"
        ):

            overview_hypertension = (
                latest_prediction.hypertension
            )

        if hasattr(
            latest_prediction,
            "heart_disease"
        ):

            overview_heart_disease = (
                latest_prediction.heart_disease
            )

        if hasattr(
            latest_prediction,
            "hba1c"
        ):

            overview_hba1c = (
                latest_prediction.hba1c
            )

    return render_template(

        "index.html",

        t=t,

        current_lang=lang,

        latest_prediction=
            latest_prediction,

        risk_probability=
            risk_probability,

        risk_tier=
            risk_tier,

        risk_tier_display=
            risk_tier_display,

        overview_glucose=
            overview_glucose,

        overview_bmi=
            overview_bmi,

        overview_age=
            overview_age,

        overview_hypertension=
            overview_hypertension,

        overview_heart_disease=
            overview_heart_disease,

        overview_hba1c=
            overview_hba1c

    )


# =========================================================
# AI RISK OVERVIEW
# =========================================================

@app.route("/risk-overview")
@login_required
def risk_overview():

    t, lang = get_t()

    latest_prediction = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .first()
    )

    # -----------------------------------------------------
    # NO PREDICTION
    # -----------------------------------------------------

    if not latest_prediction:

        return render_template(

            "risk_overview.html",

            t=t,

            current_lang=lang,

            has_prediction=False,

            latest_prediction=None,

            risk_probability=0,

            risk_angle=0,

            risk_tier="Low",

            risk_tier_display=
                t.get(
                    "risk_low",
                    "Low"
                ),

            glucose=None,

            bmi=None,

            blood_pressure=None,

            age=current_user.age or None

        )

    # -----------------------------------------------------
    # PROBABILITY
    #
    # Database stores percentage.
    # Example: 75.42 means 75.42%.
    # -----------------------------------------------------

    risk_probability = round(
        float(
            latest_prediction.probability or 0
        ),
        2
    )

    # -----------------------------------------------------
    # CIRCLE ANGLE
    # -----------------------------------------------------

    risk_angle = (
        risk_probability / 100
    ) * 360

    # -----------------------------------------------------
    # RISK TIER
    # -----------------------------------------------------

    risk_tier = (
        latest_prediction.risk_tier
    )

    risk_tier_display = (
        get_risk_tier_translated(
            risk_tier,
            t
        )
    )

    return render_template(

        "risk_overview.html",

        t=t,

        current_lang=lang,

        has_prediction=True,

        latest_prediction=
            latest_prediction,

        risk_probability=
            risk_probability,

        risk_angle=
            risk_angle,

        risk_tier=
            risk_tier,

        risk_tier_display=
            risk_tier_display,

        glucose=
            latest_prediction.glucose,

        bmi=
            latest_prediction.bmi,

        blood_pressure=
            latest_prediction.blood_pressure,

        age=
            current_user.age or None

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

        "year": [
            year
        ],

        "gender": [
            gender
        ],

        "age": [
            age
        ],

        "location": [
            location
        ],

        "race:AfricanAmerican": [
            1 if race == "AfricanAmerican"
            else 0
        ],

        "race:Asian": [
            1 if race == "Asian"
            else 0
        ],

        "race:Caucasian": [
            1 if race == "Caucasian"
            else 0
        ],

        "race:Hispanic": [
            1 if race == "Hispanic"
            else 0
        ],

        "race:Other": [
            1 if race == "Other"
            else 0
        ],

        "hypertension": [
            hypertension
        ],

        "heart_disease": [
            heart_disease
        ],

        "smoking_history": [
            smoking_history
        ],

        "bmi": [
            bmi
        ],

        "hbA1c_level": [
            hbA1c_level
        ],

        "blood_glucose_level": [
            blood_glucose_level
        ]

    })


# =========================================================
# SHAP EXPLANATION
# =========================================================

def generate_shap_contributions(
    input_data,
    t
):

    try:

        import shap

        # -------------------------------------------------
        # PIPELINE MODEL
        # -------------------------------------------------

        if hasattr(
            model,
            "named_steps"
        ):

            steps = model.named_steps

            preprocessor = None
            classifier = None

            for name, step in steps.items():

                if (
                    hasattr(
                        step,
                        "transform"
                    )
                    and not hasattr(
                        step,
                        "predict_proba"
                    )
                ):

                    preprocessor = step

                if hasattr(
                    step,
                    "predict_proba"
                ):

                    classifier = step

            if classifier is None:

                classifier = model

            # -------------------------------------------------
            # TRANSFORM DATA
            # -------------------------------------------------

            if preprocessor is not None:

                transformed_data = (
                    preprocessor.transform(
                        input_data
                    )
                )

            else:

                transformed_data = (
                    input_data
                )

            # -------------------------------------------------
            # SHAP EXPLAINER
            # -------------------------------------------------

            explainer = shap.TreeExplainer(
                classifier
            )

            shap_values = (
                explainer.shap_values(
                    transformed_data
                )
            )

            # -------------------------------------------------
            # GET VALUES
            # -------------------------------------------------

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
                        0,
                        :,
                        -1
                    ]

                elif shap_array.ndim == 2:

                    values = shap_array[0]

                else:

                    values = (
                        shap_array.flatten()
                    )

            # -------------------------------------------------
            # FEATURE NAMES
            # -------------------------------------------------

            try:

                if preprocessor is not None:

                    feature_names = list(
                        preprocessor
                        .get_feature_names_out()
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

            feature_names = (
                feature_names[:count]
            )

            # -------------------------------------------------
            # TOTAL
            # -------------------------------------------------

            total_abs = float(
                np.sum(
                    np.abs(values)
                )
            )

            if total_abs == 0:

                total_abs = 1.0

            # -------------------------------------------------
            # LABELS
            # -------------------------------------------------

            label_mapping = {

                "age":
                    t.get(
                        "age",
                        "Age"
                    ),

                "bmi":
                    t.get(
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

            # -------------------------------------------------
            # BUILD CONTRIBUTIONS
            # -------------------------------------------------

            for i in range(count):

                value = float(
                    values[i]
                )

                percent = round(

                    (
                        abs(value)
                        /
                        total_abs
                    )
                    * 100,

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

                elif (
                    "gender_" in label
                ):

                    display_label = (
                        "Gender: "
                        +
                        label.replace(
                            "gender_",
                            ""
                        )
                    )

                elif (
                    "location_" in label
                ):

                    display_label = (
                        "Location: "
                        +
                        label.replace(
                            "location_",
                            ""
                        )
                    )

                elif (
                    "smoking_history_"
                    in label
                ):

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

                key=lambda x:
                    abs(x["value"]),

                reverse=True

            )

            return contributions[:10]

        # =====================================================
        # PLAIN MODEL
        # =====================================================

        explainer = shap.TreeExplainer(
            model
        )

        shap_values = (
            explainer.shap_values(
                input_data
            )
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
                    0,
                    :,
                    -1
                ]

            elif shap_array.ndim == 2:

                values = shap_array[0]

            else:

                values = (
                    shap_array.flatten()
                )

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

        for i, value in enumerate(
            values
        ):

            if i >= len(
                feature_names
            ):

                break

            value = float(
                value
            )

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
                        )
                        * 100,

                        1

                    )

            })

        contributions.sort(

            key=lambda x:
                abs(x["value"]),

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

@app.route(
    "/predict",
    methods=["POST"]
)
@login_required
def predict():

    try:

        # -------------------------------------------------
        # INPUTS
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
        # DATAFRAME
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

            blood_glucose_level=
                blood_glucose_level

        )

        print(
            "\n===================================="
        )

        print(
            "PATIENT INPUT"
        )

        print(
            "===================================="
        )

        print(
            input_data
        )

        # -------------------------------------------------
        # MODEL
        # -------------------------------------------------

        prediction_result = (
            model.predict_proba(
                input_data
            )
        )

        probability = float(
            prediction_result[0][1]
        )

        probability_percent = round(
            probability * 100,
            2
        )

        probability_percent = max(
            0,
            min(
                100,
                probability_percent
            )
        )

        print(
            "Class 0:",
            prediction_result[0][0]
        )

        print(
            "Class 1:",
            prediction_result[0][1]
        )

        print(
            "Probability:",
            probability_percent,
            "%"
        )

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        risk_tier = get_risk_tier(
            probability
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

        recommendations = (
            get_recommendations(

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
        )

        # -------------------------------------------------
        # SAVE PREDICTION
        #
        # Database stores percentage.
        # -------------------------------------------------

        new_prediction = Prediction(

            user_id=
                current_user.id,

            glucose=
                blood_glucose_level,

            bmi=
                bmi,

            blood_pressure=
                0,

            risk_tier=
                risk_tier,

            probability=
                probability_percent

        )

        db.session.add(
            new_prediction
        )

        db.session.commit()

        print(
            "Saved probability:",
            new_prediction.probability
        )

        # -------------------------------------------------
        # SHAP
        # -------------------------------------------------

        shap_contributions = (
            generate_shap_contributions(
                input_data,
                t
            )
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return render_template(

            "result.html",

            risk_tier=
                risk_tier,

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
            "PREDICTION ERROR:",
            str(e)
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

    # -----------------------------------------------------
    # ALL PREDICTIONS
    # -----------------------------------------------------

    user_predictions = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # LATEST
    # -----------------------------------------------------

    latest_prediction = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .first()
    )

    latest_probability = 0
    latest_risk = "No Risk Data"

    latest_glucose = None
    latest_bmi = None

    latest_age = (
        current_user.age or None
    )

    if latest_prediction:

        latest_probability = float(
            latest_prediction.probability or 0
        )

        latest_risk = (
            latest_prediction.risk_tier
        )

        latest_glucose = (
            latest_prediction.glucose
        )

        latest_bmi = (
            latest_prediction.bmi
        )

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    dates = [

        p.date.strftime(
            "%d-%b-%Y"
        )

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

        t=t,

        current_lang=lang,

        predictions=
            user_predictions,

        latest_prediction=
            latest_prediction,

        latest_probability=
            latest_probability,

        latest_risk=
            latest_risk,

        latest_glucose=
            latest_glucose,

        latest_bmi=
            latest_bmi,

        latest_age=
            latest_age,

        dates=
            dates,

        glucose_values=
            glucose_values,

        bmi_values=
            bmi_values,

        risk_probabilities=
            risk_probabilities,

        risk_tiers_translated=
            risk_tiers_translated,

        table_dates=
            table_dates

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
            MEAL_PLANS[
                risk_tier
            ]["Breakfast"]
        )

        lunch_dish = random.choice(
            MEAL_PLANS[
                risk_tier
            ]["Lunch"]
        )

        dinner_dish = random.choice(
            MEAL_PLANS[
                risk_tier
            ]["Dinner"]
        )

        weekly_plan.append({

            "day":
                t.get(
                    day_key,
                    day_key.title()
                ),

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

        risk_tier=
            risk_tier,

        risk_tier_display=
            risk_tier_display,

        weekly_plan=
            weekly_plan,

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
        ).strip()

        latest_prediction = (
            Prediction.query
            .filter_by(
                user_id=current_user.id
            )
            .order_by(
                Prediction.date.desc()
            )
            .first()
        )

        if latest_prediction:

            risk_tier = (
                latest_prediction.risk_tier
            )

        else:

            risk_tier = "Unknown"

        result = get_chatbot_response(

            user_message,

            risk_tier,

            lang

        )

        reply = result.get(
            "reply"
        )

        mode = result.get(
            "mode"
        )

    return render_template(

        "chatbot.html",

        reply=reply,

        mode=mode,

        user_message=user_message,

        t=t,

        current_lang=lang

    )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.route(
    "/download-report"
)
@login_required
def download_report():

    latest_prediction = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .first()
    )

    if not latest_prediction:

        return (
            "No prediction found. "
            "Please make a prediction first."
        )

    t = TRANSLATIONS["en"]

    recommendations = (
        get_recommendations(

            {

                "blood_glucose_level":
                    latest_prediction.glucose,

                "bmi":
                    latest_prediction.bmi,

                "hbA1c_level":
                    0,

                "age":
                    float(
                        current_user.age
                        or 30
                    ),

                "hypertension":
                    0,

                "heart_disease":
                    0

            },

            t

        )
    )

    pdf_buffer = generate_health_report(

        user_name=
            current_user.name,

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
            "diabetes_report_"
            f"{current_user.name}.pdf"
        ),

        mimetype=
            "application/pdf"

    )


# =========================================================
# DOCTOR LOCATOR
# =========================================================

@app.route(
    "/doctor-locator"
)
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

        t=t,

        current_lang=lang

    )


# =========================================================
# RISK SIMULATOR
# =========================================================

@app.route(
    "/simulator"
)
@login_required
def simulator():

    t, lang = get_t()

    risk_labels = {

        "Low":
            t.get(
                "risk_low",
                "Low"
            ),

        "Medium":
            t.get(
                "risk_medium",
                "Medium"
            ),

        "High":
            t.get(
                "risk_high",
                "High"
            )

    }

    return render_template(

        "simulator.html",

        t=t,

        risk_labels=
            risk_labels,

        current_lang=
            lang

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

                "error":
                    "No input data received."

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

        prediction_result = (
            model.predict_proba(
                input_data
            )
        )

        probability = float(
            prediction_result[0][1]
        )

        probability_percent = round(
            probability * 100,
            2
        )

        probability_percent = max(
            0,
            min(
                100,
                probability_percent
            )
        )

        risk_tier = get_risk_tier(
            probability
        )

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
def exercise_videos(
    risk_tier
):

    t, lang = get_t()

    if risk_tier not in EXERCISE_VIDEOS:

        risk_tier = "Low"

    videos = (
        EXERCISE_VIDEOS[
            risk_tier
        ]
    )

    risk_tier_display = (
        get_risk_tier_translated(
            risk_tier,
            t
        )
    )

    return render_template(

        "exercise_videos.html",

        risk_tier=
            risk_tier,

        risk_tier_display=
            risk_tier_display,

        videos=
            videos,

        t=t,

        current_lang=
            lang

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
                request.form.get(
                    "height",
                    0
                )
            )

            weight = float(
                request.form.get(
                    "weight",
                    0
                )
            )

            if (
                height <= 0
                or weight <= 0
            ):

                error = t.get(
                    "bmi_invalid",
                    "Please enter valid height and weight."
                )

            else:

                height_m = (
                    height / 100
                )

                bmi = round(

                    weight
                    /
                    (
                        height_m
                        *
                        height_m
                    ),

                    2

                )

                category = (
                    get_bmi_category(
                        bmi
                    )
                )

                category = (
                    get_bmi_category_translated(
                        category,
                        t
                    )
                )

        except (
            ValueError,
            TypeError
        ):

            error = t.get(
                "bmi_invalid_numbers",
                "Please enter valid numbers."
            )

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

@app.route(
    "/medication",
    methods=["GET", "POST"]
)
@login_required
def medication():

    t, lang = get_t()

    # -----------------------------------------------------
    # ADD MEDICATION
    # -----------------------------------------------------

    if request.method == "POST":

        medicine_name = request.form.get(
            "medicine_name",
            ""
        ).strip()

        dosage = request.form.get(
            "dosage",
            ""
        ).strip()

        reminder_time = request.form.get(
            "time",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not medicine_name:

            flash(
                "Please enter the medicine name."
            )

            return redirect(
                url_for("medication")
            )

        if not reminder_time:

            flash(
                "Please select a reminder time."
            )

            return redirect(
                url_for("medication")
            )

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        new_medication = Medication(

            user_id=
                current_user.id,

            medicine_name=
                medicine_name,

            dosage=
                dosage,

            time=
                reminder_time,

            notes=
                notes

        )

        db.session.add(
            new_medication
        )

        db.session.commit()

        flash(
            "Medication reminder added successfully!"
        )

        return redirect(
            url_for("medication")
        )

    # -----------------------------------------------------
    # GET MEDICATIONS
    # -----------------------------------------------------

    medications = (
        Medication.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Medication.time.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # LATEST RISK
    # -----------------------------------------------------

    latest_prediction = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .first()
    )

    if latest_prediction:

        risk_tier = (
            latest_prediction.risk_tier
        )

        probability = float(
            latest_prediction.probability
            or 0
        )

    else:

        risk_tier = "Low"

        probability = 0

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(

        "medication.html",

        t=t,

        lang=lang,

        current_lang=lang,

        medications=
            medications,

        risk_tier=
            risk_tier,

        probability=
            probability

    )


# =========================================================
# DELETE MEDICATION
# =========================================================

@app.route(
    "/delete-medication/<int:medication_id>",
    methods=["POST"]
)
@login_required
def delete_medication(
    medication_id
):

    medication_record = (
        Medication.query
        .filter_by(

            id=medication_id,

            user_id=current_user.id

        )
        .first()
    )

    if medication_record is None:

        flash(
            "Medication not found."
        )

        return redirect(
            url_for("medication")
        )

    db.session.delete(
        medication_record
    )

    db.session.commit()

    flash(
        "Medication deleted successfully."
    )

    return redirect(
        url_for("medication")
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

    # -----------------------------------------------------
    # LATEST RISK
    # -----------------------------------------------------

    latest_prediction = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .first()
    )

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

    # -----------------------------------------------------
    # BOOK APPOINTMENT
    # -----------------------------------------------------

    if request.method == "POST":

        doctor = request.form.get(
            "doctor",
            ""
        ).strip()

        hospital = request.form.get(
            "hospital",
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

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

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

        if not hospital:

            flash(
                "Please enter hospital name."
            )

            return redirect(
                url_for("appointments")
            )

        if not appointment_date:

            flash(
                "Please select an appointment date."
            )

            return redirect(
                url_for("appointments")
            )

        if not appointment_time:

            flash(
                "Please select an appointment time."
            )

            return redirect(
                url_for("appointments")
            )

        # -------------------------------------------------
        # DATE
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
        # TIME
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
        # SAME-DAY TIME
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
        # CREATE
        # -------------------------------------------------

        new_appointment = Appointment(

            user_id=
                current_user.id,

            doctor_name=
                doctor,

            hospital=
                hospital,

            appointment_date=
                appointment_date,

            appointment_time=
                appointment_time,

            purpose=
                reason

        )

        db.session.add(
            new_appointment
        )

        db.session.commit()

        flash(
            t.get(
                "appointment_success",
                "Appointment booked successfully!"
            )
        )

        return redirect(
            url_for("appointments")
        )

    # -----------------------------------------------------
    # GET APPOINTMENTS
    # -----------------------------------------------------

    appointments_list = (
        Appointment.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Appointment.appointment_date.asc(),
            Appointment.appointment_time.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

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
    "/cancel-appointment/<int:appointment_id>",
    methods=["POST"]
)
@login_required
def cancel_appointment(
    appointment_id
):

    appointment = (
        Appointment.query
        .filter_by(

            id=appointment_id,

            user_id=current_user.id

        )
        .first()
    )

    if not appointment:

        flash(
            "Appointment not found."
        )

        return redirect(
            url_for("appointments")
        )

    db.session.delete(
        appointment
    )

    db.session.commit()

    flash(
        "Appointment cancelled successfully."
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

    predictions = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.asc()
        )
        .all()
    )

    dates = [

        p.date.strftime(
            "%d-%b-%Y"
        )

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

        current_lang=lang,

        predictions=
            predictions,

        dates=
            dates,

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

@app.route(
    "/monthly-report"
)
@login_required
def monthly_report():

    t, lang = get_t()

    predictions = (
        Prediction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Prediction.date.desc()
        )
        .all()
    )

    total_predictions = len(
        predictions
    )

    # -----------------------------------------------------
    # DEFAULTS
    # -----------------------------------------------------

    average_glucose = 0
    average_bmi = 0
    latest_risk = "No Data"
    latest_probability = 0

    # -----------------------------------------------------
    # DATA
    # -----------------------------------------------------

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

        if bmi_data:

            average_bmi = round(

                sum(bmi_data)
                /
                len(bmi_data),

                2

            )

        latest_prediction = (
            predictions[0]
        )

        latest_risk = (
            latest_prediction.risk_tier
        )

        latest_probability = float(
            latest_prediction.probability
            or 0
        )

    return render_template(

        "monthly_report.html",

        t=t,

        current_lang=lang,

        predictions=
            predictions,

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
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def initialize_database():

    with app.app_context():

        db.create_all()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        debug=True
    )
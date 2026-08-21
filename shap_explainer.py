import shap
import numpy as np
import joblib
import pandas as pd

# =========================================================
# LOAD MODEL
# =========================================================

model = joblib.load(
    "model/diabetes_model.pkl"
)


# =========================================================
# ORIGINAL MODEL FEATURES
# =========================================================

FEATURE_KEYS = [
    "year",
    "gender",
    "age",
    "location",
    "race:AfricanAmerican",
    "race:Asian",
    "race:Caucasian",
    "race:Hispanic",
    "race:Other",
    "hypertension",
    "heart_disease",
    "smoking_history",
    "bmi",
    "hbA1c_level",
    "blood_glucose_level"
]


# =========================================================
# SHAP EXPLANATION
# =========================================================

def get_shap_explanation(input_data, t):

    """
    Generate SHAP explanations for the new
    15-feature XGBoost model.

    input_data must be a pandas DataFrame
    containing the original model features.
    """

    try:

        # -------------------------------------------------
        # Check input
        # -------------------------------------------------

        if not isinstance(input_data, pd.DataFrame):

            input_data = pd.DataFrame(
                input_data,
                columns=FEATURE_KEYS
            )


        # -------------------------------------------------
        # If model is a pipeline
        # -------------------------------------------------

        if hasattr(model, "steps"):

            preprocessing = model[:-1]

            classifier = model.steps[-1][1]

            # Transform original input
            transformed_data = preprocessing.transform(
                input_data
            )

            # Get transformed feature names
            try:

                transformed_names = (
                    preprocessing
                    .get_feature_names_out()
                )

            except Exception:

                transformed_names = [
                    f"feature_{i}"
                    for i in range(
                        transformed_data.shape[1]
                    )
                ]


        else:

            classifier = model

            transformed_data = input_data.values

            transformed_names = FEATURE_KEYS


        # -------------------------------------------------
        # Convert sparse matrix if required
        # -------------------------------------------------

        if hasattr(
            transformed_data,
            "toarray"
        ):

            transformed_data = (
                transformed_data.toarray()
            )


        transformed_data = np.asarray(
            transformed_data
        )


        # -------------------------------------------------
        # SHAP Tree Explainer
        # -------------------------------------------------

        explainer = shap.TreeExplainer(
            classifier
        )

        shap_values = explainer.shap_values(
            transformed_data
        )


        # -------------------------------------------------
        # Handle different SHAP versions
        # -------------------------------------------------

        if isinstance(
            shap_values,
            list
        ):

            # Binary classification
            if len(shap_values) > 1:

                values = np.asarray(
                    shap_values[1][0]
                )

            else:

                values = np.asarray(
                    shap_values[0][0]
                )

        else:

            shap_values = np.asarray(
                shap_values
            )

            # Possible shape:
            # (1, features)
            if shap_values.ndim == 2:

                values = shap_values[0]

            # Possible shape:
            # (1, features, classes)
            elif shap_values.ndim == 3:

                values = shap_values[
                    0,
                    :,
                    1
                ]

            else:

                values = shap_values


        # -------------------------------------------------
        # Aggregate one-hot encoded features
        # -------------------------------------------------

        original_contributions = {
            feature: 0.0
            for feature in FEATURE_KEYS
        }


        for feature_name, value in zip(
            transformed_names,
            values
        ):

            value = float(value)

            matched_feature = None


            # ---------------------------------------------
            # Match transformed feature to original feature
            # ---------------------------------------------

            for original_feature in FEATURE_KEYS:

                clean_original = (
                    original_feature
                    .replace(":", "_")
                )

                if (
                    original_feature in feature_name
                    or
                    clean_original in feature_name
                ):

                    matched_feature = (
                        original_feature
                    )

                    break


            # ---------------------------------------------
            # If matched
            # ---------------------------------------------

            if matched_feature:

                original_contributions[
                    matched_feature
                ] += value


        # -------------------------------------------------
        # Create chart data
        # -------------------------------------------------

        contributions = []


        for key, value in (
            original_contributions.items()
        ):

            contributions.append({

                "label":
                    t.get(
                        key,
                        key
                    ),

                "value":
                    float(value),

                "percent":
                    0.0

            })


        # -------------------------------------------------
        # Calculate percentages
        # -------------------------------------------------

        total_abs = sum(
            abs(item["value"])
            for item in contributions
        )


        if total_abs == 0:

            total_abs = 1.0


        for item in contributions:

            item["percent"] = round(

                (
                    abs(item["value"])
                    /
                    total_abs
                )
                * 100,

                1

            )


        # -------------------------------------------------
        # Sort by importance
        # -------------------------------------------------

        contributions.sort(

            key=lambda x:
                abs(x["value"]),

            reverse=True

        )


        # -------------------------------------------------
        # Return only useful features
        # -------------------------------------------------

        contributions = [

            item
            for item in contributions
            if item["percent"] > 0

        ]


        return contributions


    except Exception as e:

        print(
            "SHAP ERROR:",
            str(e)
        )

        return []
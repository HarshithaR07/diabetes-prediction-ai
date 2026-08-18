import shap
import numpy as np
import joblib

model = joblib.load('model/diabetes_model.pkl')
scaler = joblib.load('model/scaler.pkl')

FEATURE_KEYS = ["pregnancies", "glucose", "bloodpressure", "skinthickness", "insulin", "bmi", "dpf", "age"]

explainer = shap.TreeExplainer(model)


def get_shap_explanation(input_array_scaled, t):
    shap_values = explainer.shap_values(input_array_scaled)

    if isinstance(shap_values, list):
        values = shap_values[1][0]
    else:
        values = shap_values[0]

    total_abs = float(sum(abs(v) for v in values))
    if total_abs == 0:
        total_abs = 1.0

    contributions = []
    for i, key in enumerate(FEATURE_KEYS):
        percent = round(float((abs(values[i]) / total_abs) * 100), 1)
        contributions.append({
            "label": t[key],
            "value": float(values[i]),
            "percent": float(percent)
        })

    contributions.sort(key=lambda x: abs(x["value"]), reverse=True)
    return contributions
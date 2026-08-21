import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# 1. LOAD DATASET
# ============================================================

DATA_PATH = "data/diabetes_dataset_with_notes.csv"

df = pd.read_csv(DATA_PATH)

print("\n========================================")
print("DATASET INFORMATION")
print("========================================")

print("Dataset shape:", df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names:")
print(df.columns.tolist())


# ============================================================
# 2. REMOVE UNNECESSARY COLUMN
# ============================================================

if "clinical_notes" in df.columns:

    df = df.drop(
        "clinical_notes",
        axis=1
    )

    print("\nRemoved: clinical_notes")


# ============================================================
# 3. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [

    "year",
    "gender",
    "age",
    "location",

    "hypertension",
    "heart_disease",

    "smoking_history",

    "bmi",
    "hbA1c_level",
    "blood_glucose_level",

    "diabetes"
]


missing_columns = [

    col
    for col in required_columns
    if col not in df.columns

]


if missing_columns:

    print("\n========================================")
    print("ERROR: MISSING COLUMNS")
    print("========================================")

    print(
        "The following columns are missing:"
    )

    for col in missing_columns:

        print(
            "-",
            col
        )

    raise ValueError(
        "Dataset does not contain all required columns."
    )


# ============================================================
# 4. REMOVE MISSING TARGET ROWS
# ============================================================

df = df.dropna(
    subset=["diabetes"]
)


# ============================================================
# 5. DEFINE FEATURES AND TARGET
# ============================================================

X = df.drop(
    "diabetes",
    axis=1
)

y = df["diabetes"].astype(int)


print("\n========================================")
print("FEATURES AND TARGET")
print("========================================")

print(
    "Number of features:",
    X.shape[1]
)

print(
    "Target column: diabetes"
)


print("\nTarget distribution:")
print(
    y.value_counts()
)


print("\nTarget percentage:")
print(
    y.value_counts(
        normalize=True
    ) * 100
)


# ============================================================
# 6. FEATURE LIST
# ============================================================

categorical_features = [

    "gender",

    "location",

    "smoking_history"

]


numerical_features = [

    "year",

    "age",

    "hypertension",

    "heart_disease",

    "bmi",

    "hbA1c_level",

    "blood_glucose_level"

]


# Make sure only existing columns are used

categorical_features = [

    col
    for col in categorical_features
    if col in X.columns

]


numerical_features = [

    col
    for col in numerical_features
    if col in X.columns

]


print("\n========================================")
print("FEATURE TYPES")
print("========================================")

print("\nCategorical features:")

for col in categorical_features:

    print(
        "-",
        col
    )


print("\nNumerical features:")

for col in numerical_features:

    print(
        "-",
        col
    )


# ============================================================
# 7. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.20,

    random_state=42,

    stratify=y

)


print("\n========================================")
print("TRAIN / TEST SPLIT")
print("========================================")

print(
    "Training samples:",
    len(X_train)
)

print(
    "Testing samples:",
    len(X_test)
)


# ============================================================
# 8. NUMERICAL PREPROCESSING
# ============================================================

numeric_transformer = Pipeline(

    steps=[

        (
            "imputer",

            SimpleImputer(
                strategy="median"
            )
        ),

        (
            "scaler",

            StandardScaler()
        )

    ]

)


# ============================================================
# 9. CATEGORICAL PREPROCESSING
# ============================================================

categorical_transformer = Pipeline(

    steps=[

        (
            "imputer",

            SimpleImputer(
                strategy="most_frequent"
            )
        ),

        (
            "onehot",

            OneHotEncoder(
                handle_unknown="ignore"
            )
        )

    ]

)


# ============================================================
# 10. COLUMN TRANSFORMER
# ============================================================

preprocessor = ColumnTransformer(

    transformers=[

        (
            "num",

            numeric_transformer,

            numerical_features

        ),

        (
            "cat",

            categorical_transformer,

            categorical_features

        )

    ]

)


# ============================================================
# 11. DEFINE MODELS
# ============================================================

models = {

    "Logistic Regression":

        LogisticRegression(

            max_iter=1000,

            class_weight="balanced"

        ),


    "Random Forest":

        RandomForestClassifier(

            n_estimators=200,

            random_state=42,

            class_weight="balanced",

            n_jobs=-1

        ),


    "SVM":

        SVC(

            probability=True,

            random_state=42,

            class_weight="balanced"

        ),


    "XGBoost":

        XGBClassifier(

            n_estimators=200,

            max_depth=5,

            learning_rate=0.05,

            subsample=0.8,

            colsample_bytree=0.8,

            eval_metric="logloss",

            random_state=42,

            n_jobs=-1

        )

}


# ============================================================
# 12. TRAIN AND COMPARE MODELS
# ============================================================

results = []


best_model = None

best_name = ""

best_accuracy = -1


print("\n========================================")
print("MODEL COMPARISON")
print("========================================")


for name, model in models.items():

    print(
        "\nTraining:",
        name
    )


    pipeline = Pipeline(

        steps=[

            (
                "preprocessor",

                preprocessor
            ),

            (
                "classifier",

                model
            )

        ]

    )


    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    pipeline.fit(

        X_train,

        y_train

    )


    # --------------------------------------------------------
    # PREDICT
    # --------------------------------------------------------

    y_pred = pipeline.predict(

        X_test

    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    accuracy = accuracy_score(

        y_test,

        y_pred

    )


    precision = precision_score(

        y_test,

        y_pred,

        zero_division=0

    )


    recall = recall_score(

        y_test,

        y_pred,

        zero_division=0

    )


    f1 = f1_score(

        y_test,

        y_pred,

        zero_division=0

    )


    print(

        f"Accuracy  : "
        f"{accuracy * 100:.2f}%"

    )


    print(

        f"Precision : "
        f"{precision * 100:.2f}%"

    )


    print(

        f"Recall    : "
        f"{recall * 100:.2f}%"

    )


    print(

        f"F1 Score  : "
        f"{f1 * 100:.2f}%"

    )


    results.append({

        "Model":
            name,

        "Accuracy":
            accuracy,

        "Precision":
            precision,

        "Recall":
            recall,

        "F1":
            f1

    })


    # --------------------------------------------------------
    # SELECT BEST MODEL
    # --------------------------------------------------------

    if accuracy > best_accuracy:

        best_accuracy = accuracy

        best_model = pipeline

        best_name = name


# ============================================================
# 13. MODEL PERFORMANCE TABLE
# ============================================================

results_df = pd.DataFrame(
    results
)


print("\n========================================")
print("MODEL PERFORMANCE")
print("========================================")


print(

    results_df.to_string(
        index=False
    )

)


# ============================================================
# 14. BEST MODEL
# ============================================================

print("\n========================================")
print("BEST MODEL")
print("========================================")

print(
    "Best Model:",
    best_name
)


print(

    f"Best Accuracy: "
    f"{best_accuracy * 100:.2f}%"

)


# ============================================================
# 15. FINAL PREDICTION
# ============================================================

y_pred = best_model.predict(

    X_test

)


# ============================================================
# 16. FINAL METRICS
# ============================================================

accuracy = accuracy_score(

    y_test,

    y_pred

)


precision = precision_score(

    y_test,

    y_pred,

    zero_division=0

)


recall = recall_score(

    y_test,

    y_pred,

    zero_division=0

)


f1 = f1_score(

    y_test,

    y_pred,

    zero_division=0

)


print("\n========================================")
print("FINAL MODEL EVALUATION")
print("========================================")


print(
    "Model:",
    best_name
)


print(

    f"Accuracy  : "
    f"{accuracy * 100:.2f}%"

)


print(

    f"Precision : "
    f"{precision * 100:.2f}%"

)


print(

    f"Recall    : "
    f"{recall * 100:.2f}%"

)


print(

    f"F1 Score  : "
    f"{f1 * 100:.2f}%"

)


# ============================================================
# 17. CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(

    y_test,

    y_pred

)


print("\n========================================")
print("CONFUSION MATRIX")
print("========================================")


print(cm)


# ============================================================
# 18. CLASSIFICATION REPORT
# ============================================================

print("\n========================================")
print("CLASSIFICATION REPORT")
print("========================================")


print(

    classification_report(

        y_test,

        y_pred,

        target_names=[

            "No Diabetes",

            "Diabetes"

        ],

        zero_division=0

    )

)


# ============================================================
# 19. TEST PROBABILITIES
# ============================================================

print("\n========================================")
print("SAMPLE MODEL PROBABILITIES")
print("========================================")


if hasattr(

    best_model,

    "predict_proba"

):

    sample_probabilities = (

        best_model.predict_proba(

            X_test.iloc[:10]

        )

    )


    for i, probability in enumerate(

        sample_probabilities

    ):

        print(

            f"Sample {i + 1}: "

            f"No Diabetes = "
            f"{probability[0] * 100:.2f}% | "

            f"Diabetes = "
            f"{probability[1] * 100:.2f}%"

        )


# ============================================================
# 20. SAVE MODEL
# ============================================================

MODEL_OUTPUT = (
    "model/diabetes_model.pkl"
)


joblib.dump(

    best_model,

    MODEL_OUTPUT

)


# ============================================================
# 21. SAVE MODEL INFORMATION
# ============================================================

model_info = {

    "model_name":
        best_name,

    "accuracy":
        float(accuracy),

    "precision":
        float(precision),

    "recall":
        float(recall),

    "f1_score":
        float(f1),

    "features":
        list(X.columns),

    "numerical_features":
        numerical_features,

    "categorical_features":
        categorical_features,

    "target":
        "diabetes"

}


joblib.dump(

    model_info,

    "model/model_info.pkl"

)


# ============================================================
# 22. FINAL MESSAGE
# ============================================================

print("\n========================================")
print("MODEL SAVING")
print("========================================")


print(
    "Model saved successfully:"
)


print(
    "model/diabetes_model.pkl"
)


print(
    "Model information saved:"
)


print(
    "model/model_info.pkl"
)


print("\n========================================")
print("TRAINING COMPLETED")
print("========================================")
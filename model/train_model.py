import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import joblib

# 1. Load dataset
df = pd.read_csv('data/diabetes.csv')
print("Dataset shape:", df.shape)
print(df.head())

# 2. Replace physiologically impossible zeros with NaN, then class-grouped mean
cols_with_zero_issue = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
for col in cols_with_zero_issue:
    df[col] = df[col].replace(0, np.nan)

for col in cols_with_zero_issue:
    df[col] = df.groupby('Outcome')[col].transform(lambda x: x.fillna(x.mean()))

# 3. Split features and target
X = df.drop('Outcome', axis=1)
y = df['Outcome']

# 4. Train/test split (before SMOTE, to avoid leakage)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 5. Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 6. Balance training data with SMOTE
smote = SMOTE(random_state=42)
X_train_bal, y_train_bal = smote.fit_resample(X_train_scaled, y_train)

# 7. Define models to compare
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "SVM": SVC(probability=True, random_state=42),
    "XGBoost": XGBClassifier(eval_metric='logloss', random_state=42)
}

# 8. Train, cross-validate, and evaluate each model
best_model = None
best_score = 0
best_name = ""

for name, model in models.items():
    scores = cross_val_score(model, X_train_bal, y_train_bal, cv=10, scoring='accuracy')
    mean_score = scores.mean()
    print(f"{name}: CV Accuracy = {mean_score:.4f}")

    if mean_score > best_score:
        best_score = mean_score
        best_model = model
        best_name = name

print(f"\nBest model: {best_name} with CV accuracy {best_score:.4f}")

# 9. Train the best model on the full balanced training set
best_model.fit(X_train_bal, y_train_bal)

# 10. Evaluate on the untouched test set
test_accuracy = best_model.score(X_test_scaled, y_test)
print(f"Test set accuracy: {test_accuracy:.4f}")

# 11. Save model and scaler
joblib.dump(best_model, 'model/diabetes_model.pkl')
joblib.dump(scaler, 'model/scaler.pkl')
print("\nModel and scaler saved successfully in the 'model' folder.")
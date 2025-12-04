# app/main.py
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
import numpy as np
import joblib
import os
from dotenv import load_dotenv
from .utils import log_prediction

# Charger les variables d'environnement
load_dotenv()


MODEL_PATH = os.getenv("MODEL_PATH", "app/models/best_model_GB_opt.joblib")

# Objet FastAPI que uvicorn doit trouver : app.main:app
app = FastAPI(
    title="UA2 – API Diabetes",
    description="API FastAPI exposant le modèle best_model_GB_opt (Gradient Boosting).",
    version="1.0.0"
)

# Charger le modèle une seule fois au démarrage
model = joblib.load(MODEL_PATH)


# ===== Schéma d'entrée (ajuste les noms si besoin) =====
class DiabetesInput(BaseModel):
    pregnancies: float = Field(..., description="Nombre de grossesses")
    glucose: float = Field(..., description="Taux de glucose")
    blood_pressure: float = Field(..., description="Pression sanguine")
    skin_thickness: float = Field(..., description="Épaisseur de peau")
    insulin: float = Field(..., description="Insuline")
    bmi: float = Field(..., description="IMC")
    diabetes_pedigree_function: float = Field(..., description="DPF")
    age: float = Field(..., description="Âge")


# ===================== Endpoints =====================

@app.get("/health")
def health():
    """Vérifie que l'API tourne."""
    return {"status": "ok", "message": "API opérationnelle"}


@app.get("/ready")
def ready():
    """Vérifie que le modèle est bien chargé."""
    return {"ready": model is not None}


@app.post("/predict")
def predict(data: DiabetesInput):
    """Retourne la prédiction + probabilité (si disponible)."""

    # 1) Features d'origine
    base_features = {
        "Pregnancies": data.pregnancies,
        "Glucose": data.glucose,
        "BloodPressure": data.blood_pressure,
        "SkinThickness": data.skin_thickness,
        "Insulin": data.insulin,
        "BMI": data.bmi,
        "DiabetesPedigreeFunction": data.diabetes_pedigree_function,
        "Age": data.age,
    }

    # 2) Features dérivées
    glucose_over_bmi = data.glucose / data.bmi if data.bmi != 0 else 0.0

    if data.bmi < 18.5:
        bmi_cat = "underweight"
    elif data.bmi < 25:
        bmi_cat = "normal"
    elif data.bmi < 30:
        bmi_cat = "overweight"
    else:
        bmi_cat = "obese"

    high_preg = 1 if data.pregnancies >= 5 else 0

    if data.age < 30:
        age_bin = "young"
    elif data.age < 50:
        age_bin = "middle"
    else:
        age_bin = "old"

    engineered_features = {
        "Glucose_over_BMI": glucose_over_bmi,
        "BMI_category": bmi_cat,
        "HighPreg": high_preg,
        "Age_bin": age_bin,
    }

    # 3) DataFrame complet
    all_features = {**base_features, **engineered_features}
    input_df = pd.DataFrame([all_features])

    # 4) Prédiction
    y_pred = model.predict(input_df)[0]

    if hasattr(model, "predict_proba"):
        prob = float(model.predict_proba(input_df)[0, 1])
    else:
        prob = None

    response = {
        "prediction": int(y_pred),
        "probability_positive": prob
    }

    # 5) Enregistrement de la requête et de la réponse dans le fichier JSONL
    try:
        # data.model_dump() donne le JSON d'entrée tel que reçu par FastAPI
        log_prediction(
            input_payload=data.model_dump(),
            response_payload=response,
            source="api_local"
        )
    except Exception as e:
        print(f"[main.predict] Erreur lors de la journalisation: {e}")

    return response

# Lancer l'app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
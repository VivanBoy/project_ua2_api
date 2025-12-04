# UA2 – API Diabetes (FastAPI + Docker)

Ce projet expose un modèle de classification du diabète (`best_model_GB_opt.joblib`) via une API REST construite avec **FastAPI** et déployable dans un conteneur **Docker**. Le modèle a été entraîné sur le dataset `diabetes.csv` (Pima Indians Diabetes) avec un pipeline `scikit-learn` incluant :

- Prétraitement (imputation, standardisation, encodage)
- Ingénierie de variables (features dérivées)
- Classifieur `GradientBoostingClassifier`

---

## Table des matières

1. [Structure du projet](#structure-du-projet)
2. [Installation locale (sans Docker)](#installation-locale-sans-docker)
3. [Lancer l’API en local](#lancer-lapi-en-local)
4. [Ingénierie des features côté API](#ingénierie-des-features-côté-api)
5. [Utilisation avec Docker](#utilisation-avec-docker)
6. [Arrêter / nettoyer les conteneurs](#arrêter--nettoyer-les-conteneurs)
7. [Améliorations possibles](#améliorations-possibles)

## 1. Structure du projet

```text
project_ua2_api/
├─ app/
│  ├─ main.py                 # API FastAPI (endpoints /health, /ready, /predict)
│  └─ models/
│     └─ best_model_GB_opt.joblib   # modèle entraîné sérialisé
├─ requirements.txt           # dépendances Python
├─ .env                       # variables d'environnement (chemin du modèle, etc.)
├─ Dockerfile                 # définition de l'image Docker
├─ .dockerignore              # fichiers exclus du build Docker
└─ journal_de_projet.md       # journal des étapes et choix techniques
```

## 2. Installation locale (sans Docker)

### 2.1. Créer un environnement Python

```bash
# Exemple avec venv
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# ou
.\.venv\Scripts\activate       # Windows PowerShell
```

### 2.2. Installer les dépendances

```bash
pip install -r requirements.txt
```

Vérifiez que `requirements.txt` contient notamment :

```text
fastapi
uvicorn[standard]
scikit-learn==1.6.1
joblib
numpy
pandas
python-dotenv
pydantic
```

### 2.3. Fichier .env

À la racine du projet :

```env
MODEL_PATH=app/models/best_model_GB_opt.joblib
```

## 3. Lancer l’API en local

Depuis la racine du projet :

```bash
uvicorn app.main:app --reload
```

L’API est disponible sur :  
 [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Endpoints principaux :

- **GET /health** : vérifie que l’API fonctionne.
- **GET /ready** : vérifie que le modèle est bien chargé.
- **POST /predict** : renvoie la prédiction pour un patient.

La documentation interactive est disponible ici :  
 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Exemple de requête /predict

**Body JSON :**

```json
{
    "pregnancies": 2,
    "glucose": 150,
    "blood_pressure": 70,
    "skin_thickness": 35,
    "insulin": 0,
    "bmi": 33.6,
    "diabetes_pedigree_function": 0.627,
    "age": 50
}
```

**Réponse typique :**

```json
{
    "prediction": 1,
    "probability_positive": 0.62
}
```

## 4. Ingénierie des features côté API

Le pipeline du modèle attend les colonnes suivantes :

### Features brutes :

- Pregnancies
- Glucose
- BloodPressure
- SkinThickness
- Insulin
- BMI
- DiabetesPedigreeFunction
- Age

### Features dérivées (recalculées dans l’API) :

- Glucose_over_BMI : Glucose / BMI
- BMI_category : catégorie d’IMC (underweight, normal, overweight, obese)
- HighPreg : indicateur 0/1 si Pregnancies >= 5
- Age_bin : tranche d’âge (young, middle, old)

Dans `app/main.py`, la fonction `/predict` reconstruit ces 4 variables avant d’appeler `model.predict`.

## 5. Utilisation avec Docker

### 5.1. Construire l’image

Depuis la racine du projet :

```bash
docker build -t ua2-diabetes-api .
```

### 5.2. Lancer le conteneur

```bash
docker run -d -p 8000:8000 --name ua2-diabetes-container ua2-diabetes-api
```

Vérifiez que le conteneur tourne :

```bash
docker ps
```

L’API est accessible via Docker sur :  
 [http://127.0.0.1:8000](http://127.0.0.1:8000)

Les endpoints (/health, /ready, /predict, /docs) sont les mêmes qu’en local.

## 6. Arrêter / nettoyer les conteneurs

```bash
docker stop ua2-diabetes-container
docker rm ua2-diabetes-container
```

## 7. Améliorations possibles

- Ajouter des tests automatisés (ex. pytest + httpx).
- Ajouter un endpoint `/info` pour afficher des métadonnées du modèle (date d’entraînement, métriques, etc.).
- Ajouter une gestion de logs plus détaillée (logs des requêtes, temps de réponse).
- Intégrer un système d’authentification si l’API est exposée publiquement.
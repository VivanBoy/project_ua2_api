# UA2 – API Diabetes (FastAPI + Docker)

Ce projet expose un modèle de classification du diabète (`best_model_GB_opt.joblib`) via une API REST construite avec **FastAPI** et déployable dans un conteneur **Docker**.  
Le modèle a été entraîné sur le dataset `diabetes.csv` (Pima Indians Diabetes) avec un pipeline scikit-learn incluant :

- Prétraitement (imputation, standardisation, encodage)
- Ingénierie de variables (features dérivées)
- Classifieur `GradientBoostingClassifier`

---

## Table des matières

1. [Structure du projet](#1-structure-du-projet)  
2. [Installation locale (sans Docker)](#2-installation-locale-sans-docker)  
3. [Lancer l’API en local](#3-lancer-lapi-en-local)  
4. [Ingénierie des features côté API](#4-ingénierie-des-features-côté-api)  
5. [Utilisation avec Docker](#5-utilisation-avec-docker)  
6. [Arrêter / nettoyer les conteneurs](#6-arrêter--nettoyer-les-conteneurs)  
7. [Améliorations possibles](#7-améliorations-possibles)  
8. [Déploiement en ligne (Google Cloud Run)](#8-déploiement-en-ligne-google-cloud-run)  
9. [Erreurs rencontrées et ajustements](#9-erreurs-rencontrées-et-ajustements)  

---

## 1. Structure du projet

```text
project_ua2_api/
├─ app/
│  ├─ main.py                 # API FastAPI (endpoints /, /health, /ready, /predict, /docs)
│  ├─ utils.py                # Fonction de logging (journalisation des requêtes)
│  └─ models/
│     └─ best_model_GB_opt.joblib   # Modèle entraîné sérialisé
├─ requirements.txt           # Dépendances Python
├─ .env                       # Variables d'environnement (chemin du modèle, etc.)
├─ Dockerfile                 # Définition de l'image Docker
├─ .dockerignore              # Fichiers exclus du build Docker
├─ journal_de_projet.md       # Journal des étapes et choix techniques
├─ requetes_enrg.jsonl        # (Optionnel) journal des requêtes / prédictions
└─ README.md                  # Ce document

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
### Rôle de requirements.txt :
il décrit toutes les bibliothèques nécessaires pour exécuter l’API et charger le modèle.
Il garantit que l’environnement local ou dans Docker utilise les bonnes versions de chaque package.

### 2.3. Fichier .env

À la racine du projet :

```env
MODEL_PATH=app/models/best_model_GB_opt.joblib
```
3. Lancer l’API en local

Depuis la racine du projet :
```env
uvicorn app.main:app --reload
```

L’API est disponible sur :
```env
http://127.0.0.1:8000
```
Endpoints principaux :
```text
GET / : message de bienvenue + liste des endpoints utiles

GET /health : vérifie que l’API fonctionne

GET /ready : vérifie que le modèle est bien chargé

POST /predict : renvoie la prédiction pour un patient
```
La documentation interactive est disponible ici :
```env
http://127.0.0.1:8000/docs
```
Exemple de requête /predict
```bash
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

Réponse typique :
```bash
{
  "prediction": 1,
  "probability_positive": 0.62
}
```
# 4. Ingénierie des features côté API

Le pipeline du modèle attend les colonnes suivantes :
```text
Features brutes

Pregnancies

Glucose

BloodPressure

SkinThickness

Insulin

BMI

DiabetesPedigreeFunction

Age

Features dérivées (recalculées dans l’API)

Glucose_over_BMI : Glucose / BMI

BMI_category : catégorie d’IMC (underweight, normal, overweight, obese)

HighPreg : indicateur 0/1 si Pregnancies >= 5

Age_bin : tranche d’âge (young, middle, old)
```
Dans app/main.py, la route /predict reconstruit ces 4 variables avant d’appeler model.predict().

# 5. Utilisation avec Docker
## 5.1. Rôle du Dockerfile

Le Dockerfile décrit comment construire l’image Docker de l’API.
Il :

Utilise une image de base (python:3.11-slim)

Définit un répertoire de travail /app

Copie requirements.txt et installe les dépendances avec pip

Copie le reste du projet (app/, modèle, etc.)

Lance Uvicorn avec :
```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Objectif : permettre d’exécuter l’API dans un environnement isolé et reproductible, sans avoir à installer Python / dépendances sur la machine hôte.

### 5.2. Construire l’image

Depuis la racine du projet :
```
docker build -t ua2-diabetes-api .
```
### 5.3. Lancer le conteneur
```
docker run -d -p 8000:8000 --name ua2-diabetes-container ua2-diabetes-api
```

Vérifier que le conteneur tourne :
```
docker ps
```

L’API est accessible via Docker sur :
```
http://127.0.0.1:8000
```
Les endpoints (/, /health, /ready, /predict, /docs) sont les mêmes qu’en local.

# 6. Arrêter / nettoyer les conteneurs
```
docker stop ua2-diabetes-container
docker rm ua2-diabetes-container
```
# 7. Améliorations possibles

Ajouter des tests automatisés (ex : pytest + httpx).
Ajouter un endpoint /info pour afficher des métadonnées du modèle (date d’entraînement, métriques, etc.).
Ajouter une gestion de logs plus détaillée (logs des requêtes, temps de réponse).
Intégrer un système d’authentification si l’API est exposée publiquement.

# 8. Déploiement en ligne (Google Cloud Run)

L’API a été déployée sur Google Cloud Run à partir de l’image Docker construite avec :
```
docker build -t ua2-diabetes-api .
```

et envoyée avec gcloud builds submit.
URL publique de l’API :
```
https://ua2-diabetes-api-412188004468.northamerica-northeast1.run.app
```

Endpoints disponibles en ligne :
```text
GET / : message de bienvenue + liste des endpoints utiles

GET /health : statut simple de l’API

GET /ready : vérifie que le modèle est bien chargé

POST /predict : prédiction en ligne

GET /docs : documentation Swagger hébergée sur Cloud Run
```
#### Exemple de requête /predict en ligne (PowerShell)
curl -Method POST `
  "https://ua2-diabetes-api-412188004468.northamerica-northeast1.run.app/predict" `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{
    "pregnancies": 2,
    "glucose": 150,
    "blood_pressure": 70,
    "skin_thickness": 35,
    "insulin": 0,
    "bmi": 33.6,
    "diabetes_pedigree_function": 0.627,
    "age": 50
  }'

# 9. Erreurs rencontrées et ajustements

### Compatibilité scikit-learn / modèle
Le modèle avait été entraîné avec une autre version de scikit-learn, ce qui a généré des warnings InconsistentVersionWarning au chargement.
➜ Ajustement : aligner la version de scikit-learn dans requirements.txt pour rester compatible avec le modèle sérialisé.

### Colonnes manquantes dans le pipeline
Le pipeline attendait des features dérivées (Glucose_over_BMI, BMI_category, HighPreg, Age_bin) en plus des variables brutes.
➜ Ajustement : ces colonnes sont recalculées dans l’API avant l’appel à model.predict().

### Erreur FileNotFoundError sur le modèle
Au début, le chemin vers le fichier best_model_GB_opt.joblib n’était pas correct.
➜ Ajustement : utilisation de la variable d’environnement MODEL_PATH avec une valeur par défaut app/models/best_model_GB_opt.joblib.

### Erreur 404 sur la racine de l’API en ligne
L’URL de base Cloud Run renvoyait {"detail": "Not Found"} car aucun endpoint / n’était défini.
➜ Ajustement : ajout d’une route GET / dans main.py pour afficher un message d’accueil et les endpoints utiles.

### Problèmes d’authentification gcloud (UNAUTHENTICATED)
Lors des commandes gcloud builds submit et gcloud run deploy, des erreurs 401 sont apparues.
➜ Ajustement : relancer gcloud auth login et vérifier que le projet actif était bien leafy-antonym-480105-f3 avant de relancer le build et le déploiement.


---

### Ce que tu fais maintenant

1. Ouvre `README.md` sur ton PC.
2. **Sélectionne tout** → `Ctrl + A`, puis **Supprime**.
3. Colle tout le texte ci-dessus → `Ctrl + V`.
4. Enregistre → `Ctrl + S`.

Puis dans le terminal :

```bash
cd C:\Users\Innocent\OneDrive\Documents\project_ua2_api
git status
git add README.md
git commit -m "Compléter README avec Cloud Run et erreurs rencontrées"
git push
```

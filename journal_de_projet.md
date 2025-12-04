# Journal de projet – Déploiement d’une solution IA (UA2)

## 1. Contexte et objectif

L’objectif de ce travail est de préparer mon modèle IA pour un **déploiement public** via une API web et un conteneur Docker.

Le modèle utilisé est un **Gradient Boosting** entraîné sur le dataset `diabetes.csv`.  
Le meilleur modèle sauvegardé s’appelle :

- `best_model_GB_opt.joblib`

Il est exposé via une API **FastAPI** puis dockerisé pour assurer une exécution reproductible sur n’importe quelle machine.

---

## 2. Environnement et structure du projet

Le projet est organisé dans le dossier `project_ua2_api` avec la structure suivante :

- `app/`
  - `main.py` : définition de l’API FastAPI (`/health`, `/ready`, `/predict`)
  - `models/`
    - `best_model_GB_opt.joblib` : modèle entraîné et sérialisé
- `requirements.txt` : dépendances Python du projet
- `.env` : variables d’environnement (chemin du modèle)
- `Dockerfile` : définition de l’image Docker
- `.dockerignore` : fichiers/dossiers à exclure de l’image
- `journal_de_projet.md` : ce fichier

Les principaux packages utilisés :

- `fastapi`, `uvicorn`
- `scikit-learn==1.6.1`, `joblib`
- `numpy`, `pandas`
- `python-dotenv`, `pydantic`

---

## 3. Étapes de réalisation

### 3.1. Sérialisation du modèle

1. Entraînement de plusieurs modèles de classification sur le dataset Diabetes.
2. Sélection du meilleur modèle (`GradientBoostingClassifier`) avec un pipeline scikit-learn comprenant :
   - un prétraitement (imputation, standardisation, encodage),
   - de l’ingénierie de features (cf. section 4).
3. Sérialisation du pipeline complet au format `joblib` sous le nom :
   - `best_model_GB_opt.joblib`
4. Copie de ce fichier dans `app/models/`.

### 3.2. Création de l’API FastAPI

1. Création du dossier `app/` et du fichier `main.py`.
2. Définition d’un objet FastAPI :

   ```python
   app = FastAPI(
       title="UA2 – API Diabetes",
       description="API FastAPI exposant le modèle best_model_GB_opt (Gradient Boosting).",
       version="1.0.0"
   )


3. Chargement du modèle au démarrage avec joblib.load en utilisant une variable d’environnement MODEL_PATH (gérée via .env et python-dotenv).

4. Définition du schéma d’entrée avec pydantic (DiabetesInput) contenant les 8 features brutes :

    `pregnancies`, `glucose`, `blood_pressure`, `skin_thickness`,
    `insulin`, `bmi`, `diabetes_pedigree_function`, `age`.

5. Création des endpoints :

    `GET /health` : vérifie que l’API tourne.
    `GET /ready` : vérifie que le modèle est chargé.
    `POST /predict` : reçoit un JSON, reconstruit les features, et renvoie la prédiction + la probabilité.

### 3.3. Tests locaux de l’API

1. Lancement de l’API en local :

    `uvicorn app.main:app --reload`


2. Test de `GET /health` dans le navigateur :

    `http://127.0.0.1:8000/health`

    Réponse obtenue : `{"status": "ok", "message": "API opérationnelle"}`.

3. Utilisation de l’interface automatique /docs pour tester :

    `POST /predict` avec un exemple de patient.

    Réception d’un JSON de réponse contenant :

        prediction (0 ou 1)

        probability_positive (probabilité du diabète).

# 4. Ingénierie des features dans l’API

Le pipeline entraîné attend non seulement les 8 colonnes de `diabetes.csv`, mais aussi 4 features dérivées :

    Glucose_over_BMI

    BMI_category

    HighPreg

    Age_bin

Pour être compatible avec le modèle, l’API reconstruit ces features avant d’appeler `model.predict` :

### 1. Glucose_over_BMI :
- `glucose / bmi` (avec gestion du cas où bmi = 0).

### 2. BMI_category :

- < 18.5 → "underweight"

- 18.5–25 → "normal"

- 25–30 → "overweight"

- >= 30 → "obese".

### 3. HighPreg (numérique) :

- 1 si pregnancies >= 5

- 0 sinon.

### 4. Age_bin :

- < 30 → "young"

- 30–50 → "middle"

- > 50 → "old".

L’API construit ensuite un `DataFrame pandas` avec toutes les colonnes :
`Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, Glucose_over_BMI, BMI_category, HighPreg, Age_bin`, puis appelle `model.predict` et éventuellement `model.predict_proba`.

# 5. Dockerisation
### 5.1. Création du Dockerfile

Un `Dockerfile` a été ajouté à la racine du projet :

- Image de base : python:3.11-slim

- Dossier de travail : /app

- Installation des dépendances via requirements.txt

- Copie du code de l’API et du modèle dans l’image

- Commande de démarrage :

`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

### 5.2. Fichier .dockerignore

Un fichier .dockerignore exclut les éléments inutiles :

- `__pycache__/`, `.git`, `*.pyc`, `*.ipynb`, `venv/`, `etc`.

### 5.3. Construction et exécution du conteneur

Commandes utilisées :

`docker build -t ua2-diabetes-api `.

`docker run -d -p 8000:8000 --name ua2-diabetes-container ua2-diabetes-api`

`docker ps`


Tests réalisés après lancement du conteneur :

- `http://127.0.0.1:8000/health`

- `http://127.0.0.1:8000/docs` puis appel de /predict
Les réponses sont identiques à celles de l’environnement local, ce qui confirme que la containerisation est correcte.

# 6. Problèmes rencontrés et solutions

### 1 Erreur de version scikit-learn lors du chargement du modèle

Message : incompatibilité entre la version utilisée pour entraîner (1.6.1) et la version installée (1.7.2).

Solution : fixer scikit-learn==1.6.1 dans requirements.txt et réinstaller les dépendances.

Erreur columns are missing dans le ColumnTransformer

Problème : le modèle attendait les colonnes dérivées (BMI_category, HighPreg, Age_bin, Glucose_over_BMI) qui n’étaient pas reconstruites dans l’API.

Solution : recréer ces 4 features à partir des entrées de l’utilisateur dans la fonction /predict.

Erreur Cannot use median strategy with non-numeric data: 'no'

Problème : la feature HighPreg était envoyée comme "yes" / "no", alors que le pipeline appliquait un imputer numérique (médiane).

Solution : encoder HighPreg en valeur numérique (0 ou 1) avant de passer les données au modèle.

Problèmes de JSON invalide (code 422) dans Swagger

Problème : erreur de syntaxe dans le JSON envoyé (' au lieu de ").

Solution : corriger le body avec un JSON valide, en suivant l’exemple proposé dans la doc /docs.

7. Bilan et pistes d’amélioration

Ce travail m’a permis de :

Comprendre comment passer d’un notebook d’entraînement à une API de prédiction.

Gérer la sérialisation d’un pipeline scikit-learn complet (prétraitement + modèle).

Reproduire l’ingénierie de features côté API pour rester compatible avec le modèle.

Utiliser FastAPI et Docker pour préparer un déploiement reproductible.

Améliorations possibles :

Ajouter des tests unitaires automatiques sur l’API (ex. pytest + httpx).

Ajouter un endpoint /info décrivant la version du modèle, la date d’entraînement, etc.

Ajouter une gestion de logs plus avancée et une validation métier plus stricte sur les entrées.
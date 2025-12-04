"""
utils.py
Fonctions utilitaires pour l'API :
- journalisation des requêtes et réponses dans un fichier JSON Lines.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

# Nom par défaut du fichier de logs (peut être surchargé par une variable d'environnement)
DEFAULT_LOG_PATH = Path(os.getenv("REQUEST_LOG_PATH", "requetes_enrg.jsonl"))


def log_prediction(
    input_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
    log_path: Optional[Path] = None,
    source: str = "api_local",
) -> None:
    """
    Enregistre une requête de prédiction et la réponse du modèle
    dans un fichier JSONL (1 ligne = 1 requête).

    Parameters
    ----------
    input_payload : dict
        Le JSON reçu par l'API (features d'entrée).
    response_payload : dict
        Le JSON renvoyé par l'API (prediction, probability_positive, etc.).
    log_path : Path, optional
        Chemin du fichier .jsonl (par défaut 'requetes_enrg.jsonl' à la racine).
    source : str
        Contexte d'exécution ('api_local', 'api_docker', 'test_unitaire', etc.).
    """
    if log_path is None:
        log_path = DEFAULT_LOG_PATH

    # S'assurer que le parent existe (normalement la racine du projet)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "input": input_payload,
        "response": response_payload,
    }

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        # On ne veut pas faire planter l'API juste à cause du log
        print(f"[utils.log_prediction] Erreur lors de l'écriture dans {log_path}: {e}")
# Habitat Intelligent - IFT785

Application de monitoring IoT pour maison intelligente.

## Prerequis

- Python 3.8+
- Aucune installation supplementaire (SQLite inclus avec Python)

## Installation

```bash
make setup
```

Cela va :
1. Creer environnement virtuel Python
2. Installer les dependances
3. Creer la base de donnees SQLite

## Demarrage

```bash
make run
```

Application disponible sur : http://localhost:8000

## Commandes

### Commandes principales
- `make help` : Afficher toutes les commandes disponibles
- `make setup` : Installation complete (venv + deps + DB)
- `make run` : Demarrer l'application

### Environnement
- `make venv` : Creer environnement virtuel
- `make install` : Installer les dependances
- `make init` : Creer/reinitialiser la BD

### Tests et qualite
- `make test` : Lancer les tests
- `make coverage` : Rapport de couverture de tests
- `make lint` : Verifier la qualite du code

### Nettoyage
- `make clean` : Supprimer BD et fichiers temporaires
- `make clean-all` : Nettoyage complet (inclut venv)

### Evaluation complete
- `make eval` : Lancer l'évaluation automatique


## Fonctionnalites

- Reception donnees MQTT en temps reel (ou mode simulation si serveur indisponible)
- Stockage dans SQLite
- Dashboard web avec graphiques
- Alertes temperature/consommation
- Auto-refresh toutes les 5 secondes

## Configuration Requise

# Configuration CI/CD GitLab

## Pipeline

### Stages
1. **setup** : Creation base de donnees
2. **test** : Tests, lint, complexite
3. **evaluate** : Evaluation automatique POO/SOLID
4. **report** : Commentaire sur MR

### Artifacts
- `evaluation_report.html` : Rapport detaille (1 mois)
- `evaluation_report.json` : Donnees brutes
- `htmlcov/` : Couverture tests
- `flake8_report.json` : Erreurs lint
- `complexity_report.json` : Complexite code

### Declenchement
- Push sur toutes branches : Tests + Evaluation
- Merge Request : Tests + Evaluation + Commentaire MR

## Grille Evaluation

| Critere | Poids | Description |
|---------|-------|-------------|
| Fonctionnalite | 25% | Application demarre, API repond |
| Tests | 20% | Presence, passage, couverture ≥70% |
| Qualite | 20% | Lint, complexite |
| POO/SOLID | 25% | Classes, SRP, structure |
| Organisation | 10% | Dossiers, taille fichiers |

**Note minimale**: 50/100 pour passer

## Structure

- `app.py` : Application principale
- `init_db.py` : Creation base de donnees
- `ift785_client.py` : Client MQTT (fourni)
- `templates/index.html` : Interface web
- `static/` : CSS et JavaScript
- `ci/` : Evalaution CI/CD
- `tests/` : Tests unitaires (a venir)

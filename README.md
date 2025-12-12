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


# Habitat Intelligent - Code de Base (Iteration 0)

## Description

Ce projet est le **code de base procédural** pour le cours IFT785. Vous allez le refactorer en appliquant les principes de la Programmation Orientée Objet (POO) au cours des prochaines itérations.

## Fonctionnalités Actuelles

L'application fonctionne déjà et permet de :

1. **Collecter données IoT** via MQTT (température, luminosité, mouvement, consommation)
2. **Stocker dans SQLite** toutes les lectures
3. **Calculer statistiques** par pièce (moyenne, min, max)
4. **Générer alertes** selon seuils configurés
5. **Afficher dashboard** web temps réel avec graphiques

## Installation

```bash
# Installer environnement
make setup

# Démarrer application
make run
```

Application disponible sur : http://localhost:8000

## Structure Actuelle (Procédurale)

```
habitat-intelligent/
├── app.py                    # TOUT le code (monolithique)
├── ift785_client.py          # Client MQTT (FOURNI - ne pas modifier)
├── init_db.py                # Init BD (FOURNI - ne pas modifier)
├── templates/
│   └── index.html            # Dashboard (FOURNI - ne pas modifier)
├── static/
│   ├── style.css             # Styles (FOURNI - ne pas modifier)
│   └── app.js                # JS (FOURNI - ne pas modifier)
├── Makefile                  # Commandes (FOURNI)
└── requirements.txt          # Dépendances
```

## Code à Refactorer

**Fichier principal : `app.py`**

Ce fichier contient actuellement (~300 lignes) :
- Connexion base de données
- Thread MQTT listener
- Calculs statistiques
- Détection alertes
- Endpoints API FastAPI
- Configuration

**Problèmes identifiés :**
- Tout dans un seul fichier
- Pas de séparation responsabilités
- Fonctions longues et complexes
- Difficile à tester
- Pas de réutilisation possible

## Votre Mission (Itération 1)

Transformer ce code procédural en code orienté objet :

1. **Créer des classes** (Device, Room, SensorReading, Database, AlertManager, etc.)
2. **Appliquer SOLID** (SRP, OCP, LSP, ISP, DIP)
3. **Organiser en couches** (domain/, infrastructure/, application/)
4. **Écrire tests unitaires** (couverture ≥ 70%)
5. **Maintenir fonctionnalité** (tout doit continuer à marcher)

## Fichiers Fournis (Ne Pas Modifier)

Ces fichiers sont fournis par le prof et ne seront **pas évalués** :

- `ift785_client.py` : Client MQTT avec mode simulation
- `init_db.py` : Script création base de données
- `templates/index.html` : Interface web
- `static/style.css`, `static/app.js` : Assets frontend
- `Makefile` : Commandes automatisées
- `ci/` : Infrastructure CI/CD

**Important :** Vous pouvez les utiliser mais pas les modifier. Votre note n'est pas impactée par leur qualité.

## Tests Locaux

Avant de pousser sur GitLab :

```bash
# Vérifier que l'app démarre
make run

# Lancer tests
make test

# Vérifier couverture
make coverage

# Vérifier qualité code
make lint

# Simuler évaluation
python ci/evaluate.py
```

## Remise

1. Créer branche `iteration_1`
2. Refactorer le code
3. Commits réguliers (conventionnels : feat:, fix:, refactor:)
4. Push sur GitLab
5. Créer Merge Request `iteration_1` → `main`
6. Pipeline CI/CD s'exécute automatiquement
7. Voir résultats dans commentaire MR

## Évaluation Automatique

Le pipeline GitLab évalue automatiquement :
- Fonctionnalité (25%)
- Tests (20%)
- Qualité Code (20%)
- POO/SOLID (25%)
- Organisation (10%)

**Note minimale : 50/100**

## Ressources

- Énoncé complet : `devoir_iteration_1.pdf`
- Documentation SOLID : Slides cours
- Aide : Forum cours ou bureau prof

## Conseils

1. Commencer petit (une classe à la fois)
2. Tester après chaque modification
3. Commits fréquents
4. Utiliser `make test` régulièrement
5. Travailler en équipe équilibrée


# Guide Enseignant - Iteration 0 (Code de Base)

## Objectif

L'itération 0 est le **code de base procédural** que vous fournissez aux étudiants. Elle sert à :

1. Valider que le code fonctionne avant distribution
2. Établir une baseline pour les étudiants
3. Tester le système d'exclusion des fichiers fournis

## Fichiers Exclus de l'Évaluation

Le fichier `.evaluation_exclude` liste tous les fichiers fournis aux étudiants qui ne seront **pas évalués** :

```
ift785_client.py       # Client MQTT fourni
init_db.py             # Script BD fourni
templates/             # HTML fourni
static/                # CSS/JS fournis
ci/                    # Infrastructure CI/CD
Makefile
requirements.txt
README.md
```

**Résultat :** Les étudiants ne sont **pas pénalisés** pour la qualité de ces fichiers.

## Configuration Iteration 0

`ci/iterations/iteration_0.yml` définit une évaluation simplifiée :

- **Fonctionnalité : 100%** (app démarre + API fonctionne)
- **Tests : 0%** (pas requis)
- **Qualité : 0%** (pas évaluée)
- **Git : 0%** (pas évalué)

Cette config sert uniquement à **valider que le code de base fonctionne**.

## Préparation du Dépôt pour Étudiants

### Étape 1 : Pousser Code Base

```bash
# Créer branche iteration_0
git checkout -b iteration_0

# S'assurer que tous les fichiers de base sont présents
ls -la

# Commit
git add .
git commit -m "feat: code de base procedural (iteration 0)"

# Push
git push origin iteration_0
```

### Étape 2 : Tester Pipeline

```bash
# Créer MR iteration_0 -> main
# Vérifier que pipeline passe (note devrait être ~100/100)
```

### Étape 3 : Merger sur Main

Une fois validé, merger `iteration_0` → `main` pour que les étudiants partent de cette base.

## Distribution aux Étudiants

### Option A : Fork GitLab

1. Les étudiants **forkent** votre dépôt
2. Ils héritent de la config CI/CD
3. Ils créent leur branche `iteration_1`

### Option B : Clone + Nouveau Dépôt

1. Les étudiants **clonent** votre dépôt
2. Créent leur propre dépôt GitLab
3. Copient la config CI/CD

**Recommandation :** Option A (fork) pour simplicité.

## Fichiers à Distribuer

**Package minimal pour étudiants :**

```
habitat-intelligent/
├── app.py                    # Code à refactorer
├── ift785_client.py          # Fourni
├── init_db.py                # Fourni
├── templates/                # Fourni
├── static/                   # Fourni
├── Makefile                  # Fourni
├── requirements.txt          # Fourni
├── README_ETUDIANTS.md       # Instructions
├── .gitlab-ci.yml            # Pipeline
├── .evaluation_exclude       # Exclusions
└── ci/                       # Évaluation auto
    ├── evaluate.py
    ├── post_comment.py
    ├── iterations/
    │   ├── iteration_0.yml
    │   ├── iteration_1.yml
    │   └── iteration_2.yml
    └── README.md
```

## Validation Système Exclusion

Pour vérifier que l'exclusion fonctionne :

1. **Ajouter erreur volontaire** dans `ift785_client.py`
2. **Pousser** sur `iteration_0`
3. **Vérifier** que le lint ne pénalise pas

Si erreur détectée → système d'exclusion ne fonctionne pas.

## Workflow Typique

```
iteration_0 (main)
    ↓
    Étudiants forkent
    ↓
iteration_1 (étudiants)
    ↓
    Refactoring POO
    ↓
    MR → évaluation auto
    ↓
iteration_2 (étudiants)
    ↓
    Tests + endpoints
    ↓
    MR → évaluation auto
```

## Notes Attendues Iteration 0

Pour le code de base tel quel (sans refactoring) :

- **Fonctionnalité :** ~90-100% (app marche)
- **Tests :** 0% (aucun test)
- **Qualité :** Variable (non évalué avec exclusions)
- **POO :** 0% (code procédural)

**Note globale attendue iteration_0 :** ~25-30/100 (fonctionnalité seulement)

C'est normal, c'est le point de départ avant refactoring.

## Checklist Distribution

- [ ] Code de base fonctionne (`make run`)
- [ ] Pipeline passe sur `iteration_0`
- [ ] `.evaluation_exclude` configuré
- [ ] `README_ETUDIANTS.md` à jour
- [ ] Énoncés PDF générés
- [ ] Token GitLab configuré (variable `GITLAB_TOKEN`)
- [ ] Runners actifs

## FAQ

**Q: Les étudiants peuvent modifier les fichiers exclus ?**
R: Techniquement oui, mais ce n'est pas recommandé. Précisez dans les consignes.

**Q: Comment empêcher modification fichiers fournis ?**
R: Utiliser fichier `.gitattributes` ou protection branches.

**Q: L'exclusion fonctionne pour tous les jobs ?**
R: Oui, flake8, radon et evaluate.py respectent `.evaluation_exclude`.

**Q: Peut-on exclure d'autres fichiers ?**
R: Oui, ajouter dans `.evaluation_exclude`.


**Bon refactoring !**

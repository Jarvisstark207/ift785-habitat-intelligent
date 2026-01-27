.PHONY: help venv install init run test coverage lint clean clean-all setup

# Couleurs
RED=\033[0;31m
GREEN=\033[0;32m
BLUE=\033[0;34m
YELLOW=\033[1;33m
CYAN=\033[0;36m
MAGENTA=\033[0;35m
NC=\033[0m

# Variables
VENV_DIR=venv
PYTHON=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip
PYTEST=$(VENV_DIR)/bin/pytest
DB_FILE=habitat_ift785.db
EVAL_FILE=ci/evaluate.py

help:
	@echo "$(CYAN)Commandes disponibles:$(NC)"
	@echo "  $(GREEN)make setup$(NC)       - Installation complete (venv + deps + DB)"
	@echo "  $(GREEN)make venv$(NC)        - Creer environnement virtuel"
	@echo "  $(GREEN)make install$(NC)     - Installer les dependances"
	@echo "  $(GREEN)make init$(NC)        - Initialiser la base de donnees"
	@echo "  $(GREEN)make run$(NC)         - Demarrer l'application"
	@echo "  $(GREEN)make test$(NC)        - Lancer les tests"
	@echo "  $(GREEN)make coverage$(NC)    - Rapport de couverture de tests"
	@echo "  $(GREEN)make lint$(NC)        - Verifier la qualite du code"
	@echo "  $(GREEN)make eval$(NC)        - Lancer l'evaluation automatique"
	@echo "  $(GREEN)make clean$(NC)       - Nettoyer BD et fichiers temporaires"
	@echo "  $(GREEN)make clean-all$(NC)   - Nettoyage complet (inclut venv)"

venv:
	@echo "$(BLUE)Creation environnement virtuel...$(NC)"
	@python3 -m venv $(VENV_DIR)
	@echo "$(GREEN)Environnement virtuel cree: $(VENV_DIR)$(NC)"

install: venv
	@echo "$(BLUE)Installation des dependances...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependances installees$(NC)"

init:
	@echo "$(BLUE)Initialisation de la base de donnees...$(NC)"
	@$(PYTHON) init_db.py
	@echo "$(GREEN)Base de donnees creee: $(DB_FILE)$(NC)"

run:
	@echo "$(YELLOW)========================================$(NC)"
	@echo "$(YELLOW)Demarrage de l'application...$(NC)"
	@echo "$(YELLOW)========================================$(NC)"
	@$(PYTHON) -m app.main

test:
	@echo "$(MAGENTA)Execution des tests...$(NC)"
	@if [ -d "tests" ]; then \
		$(PYTEST) tests/ -v; \
		echo "$(GREEN)Tests termines$(NC)"; \
	else \
		echo "$(YELLOW)Aucun repertoire tests/ trouve$(NC)"; \
	fi

coverage:
	@echo "$(MAGENTA)Rapport de couverture...$(NC)"
	@if [ -d "tests" ]; then \
		$(PYTEST) tests/ --cov=. --cov-report=term-missing --cov-report=html; \
		echo "$(GREEN)Rapport genere dans htmlcov/index.html$(NC)"; \
	else \
		echo "$(YELLOW)Aucun repertoire tests/ trouve$(NC)"; \
	fi

lint:
	@echo "$(MAGENTA)Verification du code...$(NC)"
	@$(PYTHON) -m flake8 app.py init_db.py --max-line-length=100 --exclude=$(VENV_DIR) 2>/dev/null || \
		echo "$(YELLOW)flake8 non installe (optionnel)$(NC)"
	@echo "$(GREEN)Verification terminee$(NC)"

eval:
	@echo "$(YELLOW)========================================$(NC)"
	@echo "$(YELLOW)Demarrage de l'evaluation automatique...$(NC)"
	@echo "$(YELLOW)========================================$(NC)"
	@$(PYTHON) $(EVAL_FILE)

clean:
	@echo "$(RED)Nettoyage des fichiers temporaires...$(NC)"
	@rm -f $(DB_FILE)
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Nettoyage termine$(NC)"

clean-all: clean
	@echo "$(RED)Suppression environnement virtuel...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)Nettoyage complet termine$(NC)"

setup: venv install init
	@echo "$(CYAN)========================================$(NC)"
	@echo "$(GREEN)Setup complet termine!$(NC)"
	@echo "$(CYAN)========================================$(NC)"
	@echo "$(YELLOW)Pour demarrer: make run$(NC)"

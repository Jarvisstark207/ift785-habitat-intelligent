#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'évaluation automatique IFT785
Supporte les branches iteration_X et iteration-X (underscore OU tiret)
"""

import ast
import json
import os
import re
import subprocess
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Symboles visuels (encodage propre)
OK   = "[OK]"
WARN = "[!!]"
FAIL = "[XX]"


# ---------------------------------------------------------------------------
# Normalisation du numéro d'itération
# ---------------------------------------------------------------------------

def _detect_iteration() -> str:
    """
    Extrait le numéro d'itération depuis le nom de branche.
    Accepte indifféremment 'iteration_6', 'iteration-6', 'iteration6'.
    Retourne '0' si aucun numéro trouvé.
    """
    branch = (
        os.getenv("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME", "")
        or os.getenv("CI_COMMIT_BRANCH", "")
        or os.getenv("ITERATION", "")
    )

    # Normaliser tirets et underscores avant la recherche
    branch_normalized = branch.replace("-", "_")
    match = re.search(r"iteration_(\d+)", branch_normalized, re.IGNORECASE)
    if match:
        return match.group(1)

    # Si ITERATION est directement un nombre
    if os.getenv("ITERATION", "").isdigit():
        return os.getenv("ITERATION")

    return "0"


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------

class CodeEvaluator:

    CONFIG_DIR = "ci/iterations"

    def __init__(self):
        self.iteration = _detect_iteration()
        self.config    = self._load_config()
        self.details   = []
        self.contributors = {}
        self.excluded_files = self._load_excluded_files()

        # Auteurs à exclure de l'évaluation (demander par le professeur)
        self.excluded_authors = {
            "ngankam",
            "kenh1601",
            "hubert.ngankam@gmail.com",
            "hubert.kenfack.ngankam@usherbrooke.ca",
            "Traore Mamoudou",
            "mamoudoudiakatraore@gmail.com",
            "mbom5234",
            "mouhamadou.mourtala.mbow@usherbrooke.ca",
        }


        print(f"\n{'='*70}")
        print(f"  EVALUATION AUTOMATIQUE IFT785 — Itération {self.iteration}")
        print(f"  {self.config.get('name', '(config non trouvée)')}")
        print(f"{'='*70}\n")

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _load_config(self) -> dict:
        """Charge le YAML de l'itération. Cherche avec _ ET avec -."""
        candidates = [
            f"{self.CONFIG_DIR}/iteration_{self.iteration}.yml",
            f"{self.CONFIG_DIR}/iteration-{self.iteration}.yml",
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)

        print(f"{WARN} Config introuvable pour itération {self.iteration}, "
              f"utilisation de iteration_1.yml par défaut")
        fallback = f"{self.CONFIG_DIR}/iteration_1.yml"
        if os.path.exists(fallback):
            with open(fallback, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _load_excluded_files(self) -> set:
        excluded = set()
        path = ".evaluation_exclude"
        if not os.path.exists(path):
            return excluded
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    excluded.add(line.rstrip("/"))
        return excluded

    def _should_exclude(self, filepath: str) -> bool:
        if any(x in filepath for x in ["venv", "test", "__pycache__", ".git"]):
            return True
        for ex in self.excluded_files:
            if ex in filepath or filepath.startswith(ex):
                return True
        return False

    # ------------------------------------------------------------------
    # Helpers AST
    # ------------------------------------------------------------------

    def _source_files(self):
        """Itère sur les fichiers Python source (hors exclusions)."""
        for p in Path(".").rglob("*.py"):
            if not self._should_exclude(str(p)):
                yield p

    def _find_classes(self) -> list:
        classes = []
        for p in self._source_files():
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
                classes += [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            except Exception:
                pass
        return classes

    def _has_inheritance(self) -> bool:
        for p in self._source_files():
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
                if any(isinstance(n, ast.ClassDef) and n.bases for n in ast.walk(tree)):
                    return True
            except Exception:
                pass
        return False

    def _avg_methods_per_class(self) -> float:
        counts = []
        for p in self._source_files():
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        counts.append(len([n for n in node.body
                                           if isinstance(n, ast.FunctionDef)]))
            except Exception:
                pass
        return sum(counts) / len(counts) if counts else 0

    def _source_content(self) -> str:
        """Retourne tout le code source concaténé (pour chercher des patterns)."""
        parts = []
        for p in self._source_files():
            try:
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Check types — Fonctionnalité
    # ------------------------------------------------------------------

    def _check_import_test(self, check: dict) -> int:
        target = check.get("target", "app")
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {target}; print('OK')"],
                capture_output=True, timeout=15
            )
            if result.returncode == 0:
                self.details.append(f"{OK} {check['name']} ({check['points']}/{check['points']})")
                return check["points"]
        except Exception:
            pass
        self.details.append(f"{FAIL} {check['name']} (0/{check['points']})")
        return 0

    def _check_class_detection(self, check: dict) -> int:
        classes = self._find_classes()
        n = len(set(classes))
        minimum = check.get("min_classes", 0)
        if n >= minimum:
            self.details.append(f"{OK} {check['name']}: {n} classes ({check['points']}/{check['points']})")
            return check["points"]
        partial = int((n / max(minimum, 1)) * check["points"])
        self.details.append(f"{WARN} {check['name']}: {n}/{minimum} classes ({partial}/{check['points']})")
        return partial

    def _check_endpoint(self, check: dict) -> int:
        """Cherche les endpoints dans le code source (recherche textuelle)."""
        content = self._source_content()
        http_methods = ["get", "post", "put", "delete", "patch"]

        def _ep_present(ep: str) -> bool:
            ep_escaped = re.escape(ep)
            pattern = r'@\w+\.(?:' + "|".join(http_methods) + r')\s*\(\s*["\']' + ep_escaped
            return bool(re.search(pattern, content))

        if "endpoint" in check:
            ep = check["endpoint"]
            if _ep_present(ep):
                self.details.append(f"{OK} {check['name']} ({check['points']}/{check['points']})")
                return check["points"]
            self.details.append(f"{FAIL} {check['name']}: {ep} absent (0/{check['points']})")
            return 0

        if "endpoints" in check:
            eps = check["endpoints"]
            found = [ep for ep in eps if _ep_present(ep)]
            ratio = len(found) / len(eps)
            pts = int(ratio * check["points"])
            sym = OK if ratio == 1 else (WARN if ratio > 0 else FAIL)
            self.details.append(
                f"{sym} {check['name']}: {len(found)}/{len(eps)} endpoints ({pts}/{check['points']})"
            )
            return pts

        return 0

    def _check_pattern_detection(self, check: dict) -> int:
        """
        Détecte les design patterns dans le code source.
        Cherche des indices structurels (héritage, noms de classes/méthodes).
        """
        content = self._source_content()
        patterns = check.get("patterns", [])

        PATTERN_HINTS = {
            "Factory":           [r"class\s+\w*Factory", r"def\s+create\b", r"def\s+make\b"],
            "Repository":        [r"class\s+\w*Repository", r"def\s+find_by", r"def\s+save\b"],
            "Observer":          [r"class\s+\w*Observer", r"def\s+notify\b", r"def\s+subscribe\b",
                                  r"def\s+update\b", r"_observers"],
            "Strategy":          [r"class\s+\w*Strategy", r"def\s+execute\b", r"class\s+\w*Context"],
            "State":             [r"class\s+\w*State", r"def\s+handle\b", r"self\._state"],
            "Adapter":           [r"class\s+\w*Adapter", r"def\s+adapt\b"],
            "Facade":            [r"class\s+\w*Facade"],
            "Proxy":             [r"class\s+\w*Proxy", r"def\s+__getattr__"],
            "Decorator":         [r"class\s+\w*Decorator", r"@wraps", r"functools\.wraps"],
            "UnitOfWork":        [r"class\s+\w*UnitOfWork", r"def\s+commit\b", r"def\s+rollback\b"],
            "DependencyInjection":[r"def\s+__init__.*repository", r"def\s+__init__.*service",
                                   r"class\s+\w*Container"],
            "ServiceLocator":    [r"class\s+\w*ServiceLocator", r"def\s+get_service\b",
                                  r"_services\s*=\s*\{"],
            "CircuitBreaker":    [r"class\s+\w*CircuitBreaker", r"pybreaker", r"circuit_breaker"],
            "Retry":             [r"tenacity", r"@retry", r"def\s+retry\b"],
            "HealthCheck":       [r"/health", r"/readiness", r"def\s+health_check\b"],
            "Metaclass":         [r"class\s+\w+\s*\(.*metaclass", r"__init_subclass__",
                                  r"__new__.*cls.*mcs"],
            "DeviceFactory":     [r"class\s+DeviceFactory", r"device_registry", r"_registry\s*=\s*\{"],
        }

        found = []
        missing = []
        for p in patterns:
            hints = PATTERN_HINTS.get(p, [re.escape(p)])
            if any(re.search(h, content, re.IGNORECASE) for h in hints):
                found.append(p)
            else:
                missing.append(p)

        ratio = len(found) / max(len(patterns), 1)
        pts = int(ratio * check["points"])
        sym = OK if ratio == 1 else (WARN if ratio > 0 else FAIL)
        detail = f"{sym} {check['name']}: {found}"
        if missing:
            detail += f" | manquants: {missing}"
        detail += f" ({pts}/{check['points']})"
        self.details.append(detail)
        return pts

    def _check_database(self, check: dict) -> int:
        """Vérifie la présence d'une configuration de base de données."""
        db_type = check.get("db_type", "sqlite")
        content = self._source_content()

        if db_type == "postgresql":
            found = bool(re.search(r"postgresql|psycopg2|asyncpg", content, re.IGNORECASE))
        else:
            found = bool(re.search(r"sqlite", content, re.IGNORECASE))

        env_url = os.getenv("DATABASE_URL", "")
        if db_type == "postgresql" and "postgresql" in env_url.lower():
            found = True

        sym = OK if found else FAIL
        pts = check["points"] if found else 0
        self.details.append(f"{sym} {check['name']} ({pts}/{check['points']})")
        return pts

    def _check_mqtt(self, check: dict) -> int:
        """Vérifie que le broker MQTT est configuré et que paho-mqtt est utilisé."""
        content = self._source_content()
        found = bool(re.search(r"mqtt|paho|mosquitto|MQTTClient", content, re.IGNORECASE))
        sym = OK if found else FAIL
        pts = check["points"] if found else 0
        self.details.append(f"{sym} {check['name']} ({pts}/{check['points']})")
        return pts

    def _check_file(self, check: dict) -> int:
        """Vérifie la présence de fichiers requis."""
        required = check.get("required_files", [])
        present = [f for f in required if os.path.exists(f)]
        ratio = len(present) / max(len(required), 1)
        pts = int(ratio * check["points"])
        sym = OK if ratio == 1 else (WARN if ratio > 0 else FAIL)
        self.details.append(
            f"{sym} {check['name']}: {len(present)}/{len(required)} fichiers ({pts}/{check['points']})"
        )
        return pts

    def _check_dockerfile(self, check: dict) -> int:
        """Vérifie la qualité du Dockerfile."""
        pts = 0
        max_pts = check["points"]
        sub_checks = check.get("checks", [])
        passed = []

        if "Dockerfile existe" in sub_checks and os.path.exists("Dockerfile"):
            passed.append("Dockerfile")
        if os.path.exists("Dockerfile"):
            content = Path("Dockerfile").read_text(errors="ignore")
            if "Image de base officielle Python" in sub_checks:
                if re.search(r"FROM\s+python:", content, re.IGNORECASE):
                    passed.append("FROM python")
            if ".dockerignore present" in sub_checks and os.path.exists(".dockerignore"):
                passed.append(".dockerignore")
            if "Image buildable sans erreur" in sub_checks:
                try:
                    r = subprocess.run(
                        ["docker", "build", "-t", "ift785-check-build", "--no-cache", "."],
                        capture_output=True, timeout=300
                    )
                    if r.returncode == 0:
                        passed.append("build OK")
                except Exception:
                    pass

        ratio = len(passed) / max(len(sub_checks), 1)
        pts = int(ratio * max_pts)
        sym = OK if ratio == 1 else (WARN if ratio > 0 else FAIL)
        self.details.append(f"{sym} {check['name']}: {passed} ({pts}/{max_pts})")
        return pts

    def _check_compose(self, check: dict) -> int:
        """Vérifie le contenu du docker-compose.yml."""
        if not os.path.exists("docker-compose.yml"):
            self.details.append(f"{FAIL} {check['name']}: docker-compose.yml absent (0/{check['points']})")
            return 0

        content = Path("docker-compose.yml").read_text(errors="ignore")
        pts = 0
        max_pts = check["points"]
        passed = []
        total_checks = 0

        # Vérifier services requis
        for svc in check.get("required_services", []):
            total_checks += 1
            name = svc["name"]
            if name in content:
                if svc.get("must_build") and "build:" in content:
                    passed.append(f"service:{name}(build)")
                elif "image_prefix" in svc and svc["image_prefix"] in content:
                    passed.append(f"service:{name}")
                elif svc.get("must_build") or "image_prefix" not in svc:
                    passed.append(f"service:{name}")

        # Vérifier features requises
        feature_patterns = {
            "volumes nommes":          r"volumes:\s*\n(?:\s+\w+:)",
            "depends_on avec condition": r"condition:\s*service_healthy",
            "healthcheck par service": r"healthcheck:",
            "env_file ou environment": r"env_file:|environment:",
        }
        for feat in check.get("required_features", []):
            total_checks += 1
            pattern = feature_patterns.get(feat, re.escape(feat))
            if re.search(pattern, content, re.IGNORECASE):
                passed.append(f"feat:{feat}")

        ratio = len(passed) / max(total_checks, 1)
        pts = int(ratio * max_pts)
        sym = OK if ratio >= 0.9 else (WARN if ratio > 0 else FAIL)
        self.details.append(f"{sym} {check['name']}: {len(passed)}/{total_checks} checks ({pts}/{max_pts})")
        return pts

    def _check_compose_up(self, check: dict) -> int:
        """Tente docker compose up et vérifie le health endpoint."""
        max_pts = check["points"]
        try:
            r = subprocess.run(
                ["docker", "compose", "up", "--build", "-d"],
                capture_output=True, timeout=300
            )
            if r.returncode != 0:
                self.details.append(f"{FAIL} {check['name']}: compose up échoué (0/{max_pts})")
                return 0

            import time
            time.sleep(check.get("wait_seconds", 20))

            import urllib.request
            endpoint = check.get("health_endpoint", "/api/health")
            url = f"http://localhost{endpoint}"
            req = urllib.request.urlopen(url, timeout=10)
            if req.status == 200:
                self.details.append(f"{OK} {check['name']}: stack opérationnelle ({max_pts}/{max_pts})")
                return max_pts
        except Exception as e:
            self.details.append(f"{FAIL} {check['name']}: {e} (0/{max_pts})")
        return 0

    def _check_deployment(self, check: dict) -> int:
        """Vérifie le nombre d'instances via docker compose ps."""
        min_instances = check.get("min_instances", 1)
        try:
            r = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(r.stdout or "[]")
            running = sum(1 for s in data if s.get("State") == "running")
            if running >= min_instances:
                self.details.append(
                    f"{OK} {check['name']}: {running} instances ({check['points']}/{check['points']})"
                )
                return check["points"]
            pts = int((running / min_instances) * check["points"])
            self.details.append(f"{WARN} {check['name']}: {running}/{min_instances} instances ({pts}/{check['points']})")
            return pts
        except Exception as e:
            self.details.append(f"{FAIL} {check['name']}: {e} (0/{check['points']})")
            return 0

    def _check_frontend(self, check: dict) -> int:
        """
        Vérifie la présence d'interfaces graphiques (bonus).
        Cherche les URLs dans les templates/fichiers statiques.
        """
        urls = check.get("urls", [])
        content = self._source_content()
        html_content = ""
        for p in Path(".").rglob("*.html"):
            if not self._should_exclude(str(p)):
                try:
                    html_content += p.read_text(errors="ignore")
                except Exception:
                    pass

        found = 0
        for url in urls:
            if url in content or url in html_content:
                found += 1

        ratio = found / max(len(urls), 1)
        pts = int(ratio * check["points"])
        sym = OK if ratio >= 1 else (WARN if ratio > 0 else FAIL)
        self.details.append(f"{sym} [BONUS] {check['name']}: {found}/{len(urls)} URLs ({pts}/{check['points']})")
        return pts

    # ------------------------------------------------------------------
    # Dispatcher principal
    # ------------------------------------------------------------------

    CHECK_DISPATCH = {
        "import_test":       "_check_import_test",
        "class_detection":   "_check_class_detection",
        "endpoint_check":    "_check_endpoint",
        "pattern_detection": "_check_pattern_detection",
        "database_check":    "_check_database",
        "mqtt_check":        "_check_mqtt",
        "file_check":        "_check_file",
        "dockerfile_check":  "_check_dockerfile",
        "compose_check":     "_check_compose",
        "compose_up_check":  "_check_compose_up",
        "deployment_check":  "_check_deployment",
        "frontend_check":    "_check_frontend",
    }

    def _run_check(self, check: dict) -> int:
        check_type = check.get("type", "")
        method_name = self.CHECK_DISPATCH.get(check_type)
        if method_name:
            return getattr(self, method_name)(check)
        self.details.append(f"{WARN} Type de check inconnu: '{check_type}' (0/{check.get('points', 0)})")
        return 0

    # ------------------------------------------------------------------
    # Évaluation des 4 critères principaux
    # ------------------------------------------------------------------

    def evaluate_functionality(self) -> float:
        cfg = self.config.get("functionality", {})
        weight = cfg.get("weight", 40)
        checks = cfg.get("checks", [])
        if not checks:
            return 0.0

        total_check_pts = sum(c["points"] for c in checks)
        earned = sum(self._run_check(c) for c in checks)

        score = (earned / max(total_check_pts, 1)) * weight
        self.details.append(f"→ Fonctionnalité: {earned}/{total_check_pts} pts bruts → {score:.1f}/{weight}")
        return score

    def evaluate_tests(self) -> float:
        cfg = self.config.get("tests", {})
        weight = cfg.get("weight", 30)
        points = 0.0

        # Structure de tests
        if "test_structure" in cfg:
            points += self._eval_test_structure(cfg)
        else:
            points += self._eval_tests_simple(cfg)

        # Couverture
        cov_share = weight * 0.30
        points += self._eval_coverage(cfg.get("min_coverage", 70), cov_share)

        score = min(points, weight)
        self.details.append(f"→ Tests: {score:.1f}/{weight}")
        return score

    def _eval_tests_simple(self, cfg: dict) -> float:
        weight = cfg.get("weight", 30)
        base = weight * 0.70
        if not os.path.exists("tests"):
            self.details.append(f"{FAIL} Répertoire tests/ absent (0/{base:.1f})")
            return 0.0
        try:
            r = subprocess.run(["pytest", "tests/", "-q"],
                               capture_output=True, timeout=120)
            if r.returncode == 0:
                self.details.append(f"{OK} Tests passent ({base:.1f}/{base:.1f})")
                return base
            self.details.append(f"{WARN} Tests échouent partiellement ({base*0.5:.1f}/{base:.1f})")
            return base * 0.5
        except Exception:
            self.details.append(f"{FAIL} Erreur exécution tests (0/{base:.1f})")
            return 0.0

    def _eval_test_structure(self, cfg: dict) -> float:
        weight = cfg.get("weight", 30)
        structure = cfg.get("test_structure", {})
        base = weight * 0.70
        total = 0.0

        for category, specs in structure.items():
            cat_share = (specs.get("weight", 0) / 100) * base
            cat_pts = 0.0

            # Fichiers requis
            required = specs.get("required_files", [])
            present = sum(1 for f in required if os.path.exists(f))
            files_ok = present / max(len(required), 1)
            cat_pts += files_ok * cat_share * 0.5
            sym = OK if files_ok == 1 else (WARN if files_ok > 0 else FAIL)
            self.details.append(f"{sym} Tests/{category} fichiers: {present}/{len(required)}")

            # Nombre de tests
            min_tests = specs.get("min_tests", 0)
            if min_tests > 0:
                n = self._count_tests(f"tests/{category}")
                ratio = min(n / min_tests, 1.0)
                cat_pts += ratio * cat_share * 0.5
                sym = OK if ratio >= 1 else (WARN if ratio > 0 else FAIL)
                self.details.append(f"{sym} Tests/{category}: {n}/{min_tests} tests")

            total += cat_pts

        return total

    def _count_tests(self, path: str) -> int:
        if not os.path.exists(path):
            return 0
        try:
            r = subprocess.run(
                ["pytest", path, "--collect-only", "-q"],
                capture_output=True, text=True, timeout=30
            )
            m = re.search(r"(\d+)\s+tests?\s+collected", r.stdout)
            return int(m.group(1)) if m else 0
        except Exception:
            return 0

    def _eval_coverage(self, min_cov: float, share: float) -> float:
        if not os.path.exists("coverage.xml"):
            self.details.append(f"{FAIL} Rapport couverture absent (0/{share:.1f})")
            return 0.0
        try:
            import xml.etree.ElementTree as ET
            cov = float(ET.parse("coverage.xml").getroot().attrib.get("line-rate", 0)) * 100
            if cov >= min_cov:
                self.details.append(f"{OK} Couverture {cov:.1f}% >= {min_cov}% ({share:.1f}/{share:.1f})")
                return share
            ratio = cov / min_cov
            pts = ratio * share
            sym = WARN if cov >= min_cov - 15 else FAIL
            self.details.append(f"{sym} Couverture {cov:.1f}% / {min_cov}% ({pts:.1f}/{share:.1f})")
            return pts
        except Exception:
            self.details.append(f"{WARN} Erreur lecture couverture (0/{share:.1f})")
            return 0.0

    def evaluate_quality(self) -> float:
        cfg = self.config.get("quality", {})
        weight = cfg.get("weight", 20)
        max_errors = cfg.get("max_flake8_errors", 10)
        max_cx = cfg.get("max_complexity", 10)
        share = weight / 2
        pts = 0.0

        # Flake8
        if os.path.exists("flake8_report.json"):
            try:
                data = json.loads(Path("flake8_report.json").read_text())
                n_err = sum(len(v) for v in data.values()) if isinstance(data, dict) else len(data)
                if n_err == 0:
                    pts += share
                    self.details.append(f"{OK} Flake8: 0 erreur ({share:.1f}/{share:.1f})")
                elif n_err <= max_errors:
                    p = share * 0.6
                    pts += p
                    self.details.append(f"{WARN} Flake8: {n_err} erreurs ({p:.1f}/{share:.1f})")
                else:
                    p = share * 0.2
                    pts += p
                    self.details.append(f"{FAIL} Flake8: {n_err} erreurs > {max_errors} ({p:.1f}/{share:.1f})")
            except Exception:
                pts += share * 0.3
                self.details.append(f"{WARN} Erreur lecture flake8 ({share*0.3:.1f}/{share:.1f})")
        else:
            self.details.append(f"{WARN} flake8_report.json absent (0/{share:.1f})")

        # Complexité
        if os.path.exists("complexity_report.json"):
            try:
                data = json.loads(Path("complexity_report.json").read_text())
                high = sum(
                    1 for fd in data.values() for func in fd
                    if func.get("complexity", 0) > max_cx
                )
                if high == 0:
                    pts += share
                    self.details.append(f"{OK} Complexité acceptable ({share:.1f}/{share:.1f})")
                elif high <= 3:
                    p = share * 0.6
                    pts += p
                    self.details.append(f"{WARN} {high} fonctions complexes ({p:.1f}/{share:.1f})")
                else:
                    p = share * 0.2
                    pts += p
                    self.details.append(f"{FAIL} {high} fonctions > CC{max_cx} ({p:.1f}/{share:.1f})")
            except Exception:
                pts += share * 0.3
                self.details.append(f"{WARN} Erreur lecture complexité ({share*0.3:.1f}/{share:.1f})")
        else:
            self.details.append(f"{WARN} complexity_report.json absent (0/{share:.1f})")

        self.details.append(f"→ Qualité: {pts:.1f}/{weight}")
        return pts

    def evaluate_git(self) -> float:
        cfg = self.config.get("git", {})
        weight = cfg.get("weight", 10)
        pts = 0.0

        self._collect_contributors()

        # Commits par personne
        min_commits = cfg.get("min_commits_per_person", 5)
        share_commits = weight * 0.40
        if self.contributors:
            short = [n for n, c in self.contributors.items() if c["commits"] < min_commits]
            if not short:
                pts += share_commits
                self.details.append(f"{OK} Commits minimum atteints par tous ({share_commits:.1f}/{share_commits:.1f})")
            else:
                pts += share_commits * 0.5
                self.details.append(f"{WARN} Commits insuffisants: {', '.join(short)} ({share_commits*0.5:.1f}/{share_commits:.1f})")

        # Équilibre
        share_balance = weight * 0.30
        balanced, ratios = self._contribution_balance(cfg.get("min_contribution_ratio", 30))
        if balanced:
            pts += share_balance
            self.details.append(f"{OK} Contribution équilibrée ({share_balance:.1f}/{share_balance:.1f})")
        else:
            pts += share_balance * 0.3
            ratio_str = ", ".join(f"{n}: {r:.0f}%" for n, r in ratios.items())
            self.details.append(f"{WARN} Déséquilibre: {ratio_str} ({share_balance*0.3:.1f}/{share_balance:.1f})")

        # Commits conventionnels
        share_conv = weight * 0.30
        conv_ratio = self._conventional_commits_ratio()
        min_conv = cfg.get("conventional_commits_ratio", 60)
        if conv_ratio >= min_conv:
            pts += share_conv
            self.details.append(f"{OK} Commits conventionnels: {conv_ratio:.0f}% ({share_conv:.1f}/{share_conv:.1f})")
        else:
            p = (conv_ratio / max(min_conv, 1)) * share_conv
            pts += p
            self.details.append(f"{WARN} Commits conventionnels: {conv_ratio:.0f}% / {min_conv}% ({p:.1f}/{share_conv:.1f})")

        self.details.append(f"→ Git: {pts:.1f}/{weight}")
        return pts

    # ------------------------------------------------------------------
    # Bonus
    # ------------------------------------------------------------------

    def evaluate_bonus(self, base_score: float) -> float:
        """
        Évalue la section bonus et retourne les points bonus
        plafonnés de façon à ne pas dépasser cap_total (défaut 100).
        """
        bonus_cfg = self.config.get("bonus")
        if not bonus_cfg:
            return 0.0

        cap = bonus_cfg.get("cap_total", 100)
        max_bonus = bonus_cfg.get("max_points", 10)
        checks = bonus_cfg.get("checks", [])

        raw_bonus = sum(self._check_frontend(c) for c in checks)
        raw_bonus = min(raw_bonus, max_bonus)

        # Plafonnement : bonus ne peut pas pousser la note au-delà de cap
        allowed = max(0.0, cap - base_score)
        applied = min(raw_bonus, allowed)

        if raw_bonus > 0:
            self.details.append(
                f"\n--- BONUS ({raw_bonus:.1f} pts bruts, {applied:.1f} pts appliqués — plafond {cap}) ---"
            )
        return applied

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    def _collect_contributors(self):
        r = subprocess.run(["git", "log", "--format=%aN|%aE", "--all"],
                           capture_output=True, text=True)
        contributors = {}
        for line in r.stdout.strip().splitlines():
            if "|" in line:
                name, email = line.split("|", 1)
                # Exclure les auteurs de la liste d'exclusion (nom ou email)
                if name in self.excluded_authors or email in self.excluded_authors:
                    continue
                contributors.setdefault(name, {"email": email, "commits": 0, "lines_added": 0})
                contributors[name]["commits"] += 1

        r2 = subprocess.run(["git", "log", "--numstat", "--format=%aN", "--all"],
                            capture_output=True, text=True)
        current = None
        for line in r2.stdout.splitlines():
            if line and "\t" not in line:
                current = line
            elif "\t" in line and current and current in contributors:
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].isdigit():
                    contributors[current]["lines_added"] += int(parts[0])

        self.contributors = contributors

    def _contribution_balance(self, min_ratio: int):
        if not self.contributors:
            return True, {}
        total = sum(c["commits"] for c in self.contributors.values())
        ratios = {n: (c["commits"] / max(total, 1)) * 100 for n, c in self.contributors.items()}
        balanced = all(r >= min_ratio for r in ratios.values())
        return balanced, ratios

    def _conventional_commits_ratio(self) -> float:
        r = subprocess.run(["git", "log", "--format=%s", "--all"],
                           capture_output=True, text=True)
        messages = [m for m in r.stdout.strip().splitlines() if m]
        if not messages:
            return 0.0
        pattern = r"^(feat|fix|docs|style|refactor|test|chore|perf|build|ci)(\(.+\))?!?:"
        ok = sum(1 for m in messages if re.match(pattern, m))
        return (ok / len(messages)) * 100

    # ------------------------------------------------------------------
    # Rapports
    # ------------------------------------------------------------------

    def _generate_html(self, data: dict) -> str:
        score = data["score"]
        color = ("#2e7d32" if score >= 70 else
                 "#f57f17" if score >= 50 else "#c62828")

        rows = ""
        for d in data["details"]:
            css = ("ok" if d.startswith(OK) else
                   "warn" if d.startswith(WARN) else
                   "bonus" if "BONUS" in d else
                   "info" if d.startswith("→") else "fail")
            rows += f'<div class="row {css}">{d}</div>\n'

        contribs = ""
        for c in data.get("contributors", []):
            contribs += (f'<div class="contributor"><b>{c["name"]}</b> '
                         f'({c["email"]}) — {c["commits"]} commits '
                         f'({c["ratio"]:.1f}%) — {c["lines_added"]} lignes</div>\n')

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>IFT785 — Itération {data["iteration"]}</title>
  <style>
    body  {{ font-family: 'Segoe UI', sans-serif; max-width: 960px;
             margin: 40px auto; padding: 20px; background: #f4f6f8; }}
    .hdr  {{ background: linear-gradient(135deg,#667eea,#764ba2);
             color:#fff; padding:28px; border-radius:12px; margin-bottom:24px; }}
    .hdr h1 {{ margin:0; font-size:26px; }}
    .hdr p  {{ margin:6px 0 0; opacity:.85; }}
    .score  {{ font-size:72px; font-weight:900; color:{color};
               text-align:center; margin:20px 0; }}
    .card   {{ background:#fff; border-radius:10px; padding:22px;
               box-shadow:0 2px 6px rgba(0,0,0,.08); margin-bottom:18px; }}
    .card h2 {{ margin-top:0; color:#444; }}
    .row {{ padding:8px 12px; margin:5px 0; border-left:4px solid #ccc;
             border-radius:4px; font-family:monospace; font-size:13px; }}
    .ok   {{ border-color:#43a047; background:#f1f8e9; }}
    .warn {{ border-color:#fb8c00; background:#fff8e1; }}
    .fail {{ border-color:#e53935; background:#ffebee; }}
    .bonus{{ border-color:#8e24aa; background:#f3e5f5; }}
    .info {{ border-color:#1e88e5; background:#e3f2fd; font-weight:bold; }}
    .contributor {{ padding:8px 0; border-bottom:1px solid #eee; }}
    .bal  {{ display:inline-block; padding:4px 14px; border-radius:20px;
             background:{('#43a047' if data.get('contribution_balanced') else '#fb8c00')};
             color:#fff; margin-top:10px; font-size:13px; }}
    .scores {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
    .sc   {{ background:#f8f9fa; border-left:4px solid #667eea;
             padding:14px; border-radius:6px; }}
    .sc b {{ display:block; color:#555; font-size:12px; text-transform:uppercase; }}
    .sc span {{ font-size:24px; color:#667eea; font-weight:700; }}
  </style>
</head>
<body>
  <div class="hdr">
    <h1>IFT785 — Itération {data['iteration']}: {data['iteration_name']}</h1>
    <p>Évaluation du {data['date'][:10]}</p>
  </div>

  <div class="score">{score:.1f}/100</div>

  <div class="card">
    <h2>Résultats par critère</h2>
    <div class="scores">
      <div class="sc"><b>Fonctionnalité</b>
        <span>{data['scores']['functionality']:.1f}/{data['weights']['functionality']}</span></div>
      <div class="sc"><b>Tests</b>
        <span>{data['scores']['tests']:.1f}/{data['weights']['tests']}</span></div>
      <div class="sc"><b>Qualité Code</b>
        <span>{data['scores']['quality']:.1f}/{data['weights']['quality']}</span></div>
      <div class="sc"><b>Git</b>
        <span>{data['scores']['git']:.1f}/{data['weights']['git']}</span></div>
    </div>
    {"<br><i>Bonus appliqué : +" + f"{data['bonus']:.1f} pts</i>" if data['bonus'] > 0 else ""}
  </div>

  <div class="card">
    <h2>Équipe</h2>
    {contribs}
    <span class="bal">Contribution: {'Équilibrée' if data.get('contribution_balanced') else 'Déséquilibrée'}</span>
  </div>

  <div class="card">
    <h2>Détails</h2>
    {rows}
  </div>
</body>
</html>"""

    def generate_reports(self, scores: dict, bonus: float):
        final = scores["_total"]
        balanced, ratios = self._contribution_balance(
            self.config.get("git", {}).get("min_contribution_ratio", 30)
        )

        data = {
            "iteration":            self.iteration,
            "iteration_name":       self.config.get("name", ""),
            "date":                 datetime.now().isoformat(),
            "score":                final,
            "bonus":                bonus,
            "scores":               {k: v for k, v in scores.items() if k != "_total"},
            "weights": {
                "functionality": self.config.get("functionality", {}).get("weight", 40),
                "tests":         self.config.get("tests", {}).get("weight", 30),
                "quality":       self.config.get("quality", {}).get("weight", 20),
                "git":           self.config.get("git", {}).get("weight", 10),
            },
            "contributors": [
                {"name": n, "email": c["email"], "commits": c["commits"],
                 "lines_added": c["lines_added"], "ratio": ratios.get(n, 0)}
                for n, c in self.contributors.items()
            ],
            "contribution_balanced": balanced,
            "details": self.details,
        }

        json_file = f"evaluation_iteration_{self.iteration}.json"
        html_file = f"evaluation_iteration_{self.iteration}.html"

        Path(json_file).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        Path(html_file).write_text(self._generate_html(data), encoding="utf-8")
        print(f"\n{OK} Rapports générés: {json_file}, {html_file}")

    # ------------------------------------------------------------------
    # Point d'entrée
    # ------------------------------------------------------------------

    def run(self):
        scores = {
            "functionality": self.evaluate_functionality(),
            "tests":         self.evaluate_tests(),
            "quality":       self.evaluate_quality(),
            "git":           self.evaluate_git(),
        }
        base = sum(scores.values())
        bonus = self.evaluate_bonus(base)
        final = min(base + bonus, 100.0)
        scores["_total"] = final

        print("\n--- RÉSULTATS PAR CRITÈRE ---\n")
        weights = {
            "functionality": self.config.get("functionality", {}).get("weight", 40),
            "tests":         self.config.get("tests", {}).get("weight", 30),
            "quality":       self.config.get("quality", {}).get("weight", 20),
            "git":           self.config.get("git", {}).get("weight", 10),
        }
        for k, label in [("functionality","Fonctionnalité"),
                          ("tests","Tests"),
                          ("quality","Qualité Code"),
                          ("git","Git/Commits")]:
            print(f"  {label:20s}: {scores[k]:5.1f} / {weights[k]}")

        if bonus > 0:
            print(f"  {'Bonus':20s}: +{bonus:.1f}")

        print(f"\n{'='*50}")
        print(f"  NOTE FINALE : {final:.1f} / 100")
        print(f"{'='*50}\n")

        print("--- ÉQUIPE ---\n")
        balanced, ratios = self._contribution_balance(
            self.config.get("git", {}).get("min_contribution_ratio", 30)
        )
        for name, info in self.contributors.items():
            print(f"  {name} ({info['email']})")
            print(f"    {info['commits']} commits ({ratios.get(name, 0):.1f}%) "
                  f"— {info['lines_added']} lignes ajoutées")
        print(f"\n  Équilibre: {OK if balanced else FAIL}\n")

        print("--- DÉTAILS ---\n")
        for d in self.details:
            print(f"  {d}")

        self.generate_reports(scores, bonus)
        return final


# ---------------------------------------------------------------------------
# Entrée
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    evaluator = CodeEvaluator()
    final_score = evaluator.run()
    sys.exit(0 if final_score >= 50 else 1)

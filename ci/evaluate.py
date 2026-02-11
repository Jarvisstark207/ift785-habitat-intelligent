#!/usr/bin/env python3
"""
Script d'evaluation automatique avec configuration par iteration
"""

import json
import os
import ast
import subprocess
import yaml
from pathlib import Path
from datetime import datetime


class CodeEvaluator:
    def __init__(self):
        self.iteration = os.getenv("ITERATION", "1")
        self.config = self.load_iteration_config()
        self.score = 0
        self.max_score = 100
        self.details = []
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

    def _load_excluded_files(self):
        """Charge liste fichiers a exclure de l'evaluation"""
        excluded = set()
        exclude_file = ".evaluation_exclude"

        if not os.path.exists(exclude_file):
            return excluded

        with open(exclude_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    excluded.add(line.rstrip("/"))

        return excluded

    def _should_exclude_file(self, filepath):
        """Verifie si un fichier doit etre exclu"""
        filepath_str = str(filepath)

        # Exclusions systeme
        if any(x in filepath_str for x in ["venv", "test", "__pycache__", ".git"]):
            return True

        # Exclusions configurees
        for excluded in self.excluded_files:
            if excluded in filepath_str or filepath_str.startswith(excluded):
                return True

        return False

    def load_iteration_config(self):
        """Charge config iteration"""
        config_file = f"ci/iterations/iteration_{self.iteration}.yml"
        if not os.path.exists(config_file):
            print(f"Config {config_file} introuvable, utilisation iteration 1")
            config_file = "ci/iterations/iteration_1.yml"

        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    def get_contributors(self):
        """Extrait contributeurs et statistiques"""
        result = subprocess.run(
            ["git", "log", "--format=%aN|%aE", "--all"], capture_output=True, text=True
        )

        contributors = {}
        for line in result.stdout.strip().split("\n"):
            if "|" in line and line.strip():
                name, email = line.split("|")

                # NOUVEAU: Ignorer les auteurs exclus (prof)
                if name in self.excluded_authors or email in self.excluded_authors:
                    continue

                if name not in contributors:
                    contributors[name] = {
                        "email": email,
                        "commits": 0,
                        "lines_added": 0,
                    }
                contributors[name]["commits"] += 1

        # Stats lignes par auteur
        result = subprocess.run(
            ["git", "log", "--numstat", "--format=%aN", "--all"],
            capture_output=True,
            text=True,
        )

        current_author = None
        for line in result.stdout.split("\n"):
            if line and "\t" not in line:
                current_author = line
                # NOUVEAU: Ignorer si auteur exclu
                if current_author in self.excluded_authors:
                    current_author = None
            elif "\t" in line and current_author:
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].isdigit():
                    contributors[current_author]["lines_added"] += int(parts[0])

        self.contributors = contributors
        return contributors

    def analyze_contribution_balance(self):
        """Verifie equilibre contribution"""
        if not self.contributors:
            return False, {}

        total_commits = sum(c["commits"] for c in self.contributors.values())
        ratios = {
            name: round((c["commits"] / total_commits) * 100, 1)
            for name, c in self.contributors.items()
        }

        min_ratio = self.config["git"].get("min_contribution_ratio", 30)
        balanced = min(ratios.values()) >= min_ratio

        return balanced, ratios

    def check_conventional_commits(self):
        """Verifie format commits conventionnels"""
        result = subprocess.run(
            ["git", "log", "--format=%s", "--all"], capture_output=True, text=True
        )

        messages = result.stdout.strip().split("\n")
        conventional_pattern = (
            r"^(feat|fix|docs|style|refactor|test|chore|perf)(\(.+\))?:"
        )

        import re

        conventional_count = sum(
            1 for msg in messages if re.match(conventional_pattern, msg)
        )

        ratio = (conventional_count / len(messages)) * 100 if messages else 0
        return ratio

    def evaluate_functionality(self):
        """Evalue fonctionnalite selon config"""
        points = 0
        weight = self.config["functionality"]["weight"]
        checks = self.config["functionality"]["checks"]

        total_check_points = sum(c["points"] for c in checks)

        for check in checks:
            check_points = 0
            check_type = check["type"]

            if check_type == "import_test":
                try:
                    result = subprocess.run(
                        ["python", "-c", f'import {check["target"]}; print("OK")'],
                        capture_output=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        check_points = check["points"]
                        self.details.append(
                            f"✓ {check['name']} ({check_points}/{check['points']})"
                        )
                    else:
                        self.details.append(f"✗ {check['name']} (0/{check['points']})")
                except:
                    self.details.append(
                        f"✗ {check['name']} - erreur (0/{check['points']})"
                    )

            elif check_type == "class_detection":
                classes_found = self._find_classes()
                num_classes = len(classes_found)
                min_classes = check.get("min_classes", 0)

                if num_classes >= min_classes:
                    check_points = check["points"]
                    self.details.append(
                        f"✓ {check['name']}: {num_classes} classes ({check_points}/{check['points']})"
                    )
                else:
                    partial = int((num_classes / min_classes) * check["points"])
                    check_points = partial
                    self.details.append(
                        f"⚠ {check['name']}: {num_classes}/{min_classes} classes ({partial}/{check['points']})"
                    )

            elif check_type == "endpoint_check":
                if os.path.exists("app.py"):
                    with open("app.py", "r") as f:
                        content = f.read()

                        # Support endpoint unique ou multiple
                        if "endpoint" in check:
                            # Endpoint unique
                            endpoint = check["endpoint"]
                            if (
                                f'@app.get("{endpoint}")' in content
                                or f"@app.get('{endpoint}')" in content
                                or f'@app.post("{endpoint}")' in content
                                or f"@app.post('{endpoint}')" in content
                            ):
                                check_points = check["points"]
                                self.details.append(
                                    f"✓ {check['name']} ({check_points}/{check['points']})"
                                )
                            else:
                                self.details.append(
                                    f"✗ {check['name']} (0/{check['points']})"
                                )

                        elif "endpoints" in check:
                            # Endpoints multiples
                            endpoints = check["endpoints"]
                            found = []
                            for ep in endpoints:
                                if (
                                    f'@app.get("{ep}")' in content
                                    or f"@app.get('{ep}')" in content
                                    or f'@app.post("{ep}")' in content
                                    or f"@app.post('{ep}')" in content
                                ):
                                    found.append(ep)

                            if len(found) == len(endpoints):
                                check_points = check["points"]
                                self.details.append(
                                    f"✓ {check['name']}: tous presents ({check_points}/{check['points']})"
                                )
                            elif len(found) > 0:
                                partial = int(
                                    (len(found) / len(endpoints)) * check["points"]
                                )
                                check_points = partial
                                self.details.append(
                                    f"⚠ {check['name']}: {len(found)}/{len(endpoints)} endpoints ({partial}/{check['points']})"
                                )
                            else:
                                self.details.append(
                                    f"✗ {check['name']}: aucun endpoint (0/{check['points']})"
                                )

            elif check_type == "pattern_detection":
                patterns = check.get("patterns", [])
                found_patterns = self._detect_patterns(patterns)
                num_found = len(found_patterns)
                num_required = len(patterns)

                if num_found == num_required:
                    check_points = check["points"]
                    patterns_str = ", ".join(found_patterns)
                    self.details.append(
                        f"✓ {check['name']}: {patterns_str} ({check_points}/{check['points']})"
                    )
                elif num_found > 0:
                    partial = int((num_found / num_required) * check["points"])
                    check_points = partial
                    patterns_str = ", ".join(found_patterns)
                    self.details.append(
                        f"⚠ {check['name']}: {patterns_str} ({num_found}/{num_required}) ({partial}/{check['points']})"
                    )
                else:
                    self.details.append(
                        f"✗ {check['name']}: aucun pattern detecte (0/{check['points']})"
                    )

            points += check_points

        score = (points / total_check_points) * weight
        return score

    def evaluate_tests(self):
        """Evalue tests selon config"""
        points = 0
        weight = self.config["tests"]["weight"]

        # Verification structure tests si definie
        if "test_structure" in self.config["tests"]:
            points += self._evaluate_test_structure()
        else:
            # Mode simple (iteration 1)
            points += self._evaluate_tests_simple()

        # Couverture (toujours evaluee)
        min_cov = self.config["tests"]["min_coverage"]
        if os.path.exists("coverage.xml"):
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse("coverage.xml")
                coverage = float(tree.getroot().attrib.get("line-rate", 0)) * 100

                cov_weight = weight * 0.3
                if coverage >= min_cov:
                    points += cov_weight
                    self.details.append(
                        f"✓ Couverture {coverage:.1f}% >= {min_cov}% ({cov_weight:.1f}/{cov_weight:.1f})"
                    )
                elif coverage >= min_cov - 20:
                    partial = cov_weight * 0.6
                    points += partial
                    self.details.append(
                        f"⚠ Couverture {coverage:.1f}% ({partial:.1f}/{cov_weight:.1f})"
                    )
                else:
                    partial = cov_weight * 0.3
                    points += partial
                    self.details.append(
                        f"✗ Couverture {coverage:.1f}% < {min_cov-20}% ({partial:.1f}/{cov_weight:.1f})"
                    )
            except:
                self.details.append(f"✗ Erreur couverture (0/{weight*0.3:.1f})")
        else:
            self.details.append(f"✗ Rapport couverture absent (0/{weight*0.3:.1f})")

        return points

    def _evaluate_tests_simple(self):
        """Evaluation simple tests (iteration 1)"""
        points = 0
        weight = self.config["tests"]["weight"]

        if os.path.exists("tests"):
            try:
                result = subprocess.run(
                    ["pytest", "tests/", "-v"], capture_output=True, timeout=60
                )
                if result.returncode == 0:
                    points += weight * 0.7
                    self.details.append(
                        f"✓ Tests passent ({weight*0.7:.1f}/{weight*0.7:.1f})"
                    )
                else:
                    points += weight * 0.35
                    self.details.append(
                        f"⚠ Tests echouent partiellement ({weight*0.35:.1f}/{weight*0.7:.1f})"
                    )
            except:
                self.details.append(f"✗ Erreur tests (0/{weight*0.7:.1f})")
        else:
            self.details.append(f"✗ Repertoire tests/ absent (0/{weight*0.7:.1f})")

        return points

    def _evaluate_test_structure(self):
        """Evaluation structure tests detaillee (iteration 2+)"""
        points = 0
        weight = self.config["tests"]["weight"]
        structure = self.config["tests"]["test_structure"]

        for category, specs in structure.items():
            cat_weight = (specs["weight"] / 100) * weight * 0.7
            cat_points = 0

            # Verifier fichiers requis
            required_files = specs.get("required_files", [])
            files_present = sum(1 for f in required_files if os.path.exists(f))

            if files_present == len(required_files):
                cat_points += cat_weight * 0.5
                self.details.append(
                    f"✓ Tests {category}: fichiers presents ({cat_weight*0.5:.1f})"
                )
            elif files_present > 0:
                partial = (files_present / len(required_files)) * cat_weight * 0.5
                cat_points += partial
                self.details.append(
                    f"⚠ Tests {category}: {files_present}/{len(required_files)} fichiers ({partial:.1f})"
                )
            else:
                self.details.append(
                    f"✗ Tests {category}: fichiers manquants (0/{cat_weight*0.5:.1f})"
                )

            # Compter tests dans categorie
            min_tests = specs.get("min_tests", 0)
            if min_tests > 0:
                test_count = self._count_tests_in_category(category)

                if test_count >= min_tests:
                    cat_points += cat_weight * 0.5
                    self.details.append(
                        f"✓ Tests {category}: {test_count} tests ({cat_weight*0.5:.1f})"
                    )
                elif test_count > 0:
                    partial = (test_count / min_tests) * cat_weight * 0.5
                    cat_points += partial
                    self.details.append(
                        f"⚠ Tests {category}: {test_count}/{min_tests} tests ({partial:.1f})"
                    )
                else:
                    self.details.append(
                        f"✗ Tests {category}: aucun test (0/{cat_weight*0.5:.1f})"
                    )

            points += cat_points

        return points

    def _count_tests_in_category(self, category):
        """Compte tests dans une categorie"""
        category_path = f"tests/{category}"
        if not os.path.exists(category_path):
            return 0

        try:
            result = subprocess.run(
                ["pytest", category_path, "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            lines = result.stdout.split("\n")
            for line in lines:
                if "test" in line.lower() and ("selected" in line.lower() or "collected" in line.lower()):
                    import re

                    match = re.search(r"(\d+)\s+test", line)
                    if match:
                        return int(match.group(1))
            return 0
        except:
            return 0

    def evaluate_quality(self):
        """Evalue qualite code selon config"""
        points = 0
        weight = self.config["quality"]["weight"]
        max_errors = self.config["quality"]["max_flake8_errors"]
        max_complexity = self.config["quality"]["max_complexity"]

        # Flake8
        if os.path.exists("flake8_report.json"):
            try:
                with open("flake8_report.json", "r") as f:
                    errors = json.load(f)
                    total_errors = sum(len(v) for v in errors.values())

                    if total_errors == 0:
                        points += weight * 0.5
                        self.details.append(
                            f"✓ Flake8: 0 erreur ({weight*0.5:.1f}/{weight*0.5:.1f})"
                        )
                    elif total_errors <= max_errors:
                        partial = weight * 0.3
                        points += partial
                        self.details.append(
                            f"⚠ Flake8: {total_errors} erreurs ({partial:.1f}/{weight*0.5:.1f})"
                        )
                    else:
                        points += weight * 0.1
                        self.details.append(
                            f"✗ Flake8: {total_errors} erreurs ({weight*0.1:.1f}/{weight*0.5:.1f})"
                        )
            except:
                points += weight * 0.25
                self.details.append(
                    f"⚠ Erreur flake8 ({weight*0.25:.1f}/{weight*0.5:.1f})"
                )

        # Complexite
        if os.path.exists("complexity_report.json"):
            try:
                with open("complexity_report.json", "r") as f:
                    data = json.load(f)
                    high_complexity = sum(
                        1
                        for file_data in data.values()
                        for func in file_data
                        if func.get("complexity", 0) > max_complexity
                    )

                    if high_complexity == 0:
                        points += weight * 0.5
                        self.details.append(
                            f"✓ Complexite acceptable ({weight*0.5:.1f}/{weight*0.5:.1f})"
                        )
                    elif high_complexity <= 3:
                        partial = weight * 0.3
                        points += partial
                        self.details.append(
                            f"⚠ {high_complexity} fonctions complexes ({partial:.1f}/{weight*0.5:.1f})"
                        )
                    else:
                        points += weight * 0.1
                        self.details.append(
                            f"✗ {high_complexity} fonctions complexes ({weight*0.1:.1f}/{weight*0.5:.1f})"
                        )
            except:
                points += weight * 0.25
                self.details.append(
                    f"⚠ Erreur complexite ({weight*0.25:.1f}/{weight*0.5:.1f})"
                )

        return points

    def evaluate_git(self):
        """Evalue pratiques Git"""
        points = 0
        weight = self.config["git"]["weight"]

        self.get_contributors()

        # Commits par personne
        min_commits = self.config["git"]["min_commits_per_person"]
        all_meet = all(c["commits"] >= min_commits for c in self.contributors.values())

        if all_meet:
            points += weight * 0.4
            self.details.append(
                f"✓ Commits minimums atteints ({weight*0.4:.1f}/{weight*0.4:.1f})"
            )
        else:
            below = [
                n for n, c in self.contributors.items() if c["commits"] < min_commits
            ]
            points += weight * 0.2
            self.details.append(
                f"⚠ Commits insuffisants pour: {', '.join(below)} ({weight*0.2:.1f}/{weight*0.4:.1f})"
            )

        # Equilibre contribution
        balanced, ratios = self.analyze_contribution_balance()
        if balanced:
            points += weight * 0.3
            self.details.append(
                f"✓ Contribution equilibree ({weight*0.3:.1f}/{weight*0.3:.1f})"
            )
        else:
            points += weight * 0.1
            ratio_str = ", ".join(f"{n}: {r}%" for n, r in ratios.items())
            self.details.append(
                f"⚠ Desequilibre: {ratio_str} ({weight*0.1:.1f}/{weight*0.3:.1f})"
            )

        # Commits conventionnels
        conv_ratio = self.check_conventional_commits()
        min_conv = self.config["git"]["conventional_commits_ratio"]

        if conv_ratio >= min_conv:
            points += weight * 0.3
            self.details.append(
                f"✓ Commits conventionnels: {conv_ratio:.0f}% ({weight*0.3:.1f}/{weight*0.3:.1f})"
            )
        else:
            partial = (conv_ratio / min_conv) * weight * 0.3
            points += partial
            self.details.append(
                f"⚠ Commits conventionnels: {conv_ratio:.0f}% ({partial:.1f}/{weight*0.3:.1f})"
            )

        return points

    def _find_classes(self):
        """Trouve toutes les classes dans le code"""
        classes = []
        for py_file in Path(".").rglob("*.py"):
            if self._should_exclude_file(py_file):
                continue
            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes.append(node.name)
            except:
                continue
        return classes

    def _detect_patterns(self, patterns):
        """Detecte patterns de conception (Factory, Repository, Observer, etc.)"""
        found = []
        pattern_keywords = {
            "Factory": ["Factory", "factory"],
            "Repository": ["Repository", "repository", "Repo"],
            "Observer": ["Observer", "observer", "Listener", "listener"],
        }

        for pattern in patterns:
            keywords = pattern_keywords.get(pattern, [pattern])
            detected = False

            # Chercher dans les fichiers Python
            for py_file in Path(".").rglob("*.py"):
                if self._should_exclude_file(py_file):
                    continue
                try:
                    with open(py_file, "r") as f:
                        content = f.read()
                        # Chercher le pattern dans les noms de classe ou en commentaires
                        for keyword in keywords:
                            if keyword in content:
                                detected = True
                                break
                except:
                    continue

                if detected:
                    break

            if detected:
                found.append(pattern)

        return found

    def run_evaluation(self):
        """Execute evaluation complete"""
        print("\n" + "=" * 70)
        print(f"EVALUATION AUTOMATIQUE - ITERATION {self.iteration}")
        print(f"{self.config['name']}")
        print("=" * 70 + "\n")

        scores = {
            "functionality": self.evaluate_functionality(),
            "tests": self.evaluate_tests(),
            "quality": self.evaluate_quality(),
            "git": self.evaluate_git(),
        }

        total_score = sum(scores.values())

        print("\n--- RESULTATS PAR CRITERE ---\n")
        print(
            f"{'Fonctionnalite':20s}: {scores['functionality']:.1f}/{self.config['functionality']['weight']}"
        )
        print(f"{'Tests':20s}: {scores['tests']:.1f}/{self.config['tests']['weight']}")
        print(
            f"{'Qualite Code':20s}: {scores['quality']:.1f}/{self.config['quality']['weight']}"
        )
        print(
            f"{'Git/Commits':20s}: {scores['git']:.1f}/{self.config['git']['weight']}"
        )

        print(f"\n{'='*70}")
        print(f"NOTE FINALE: {total_score:.1f}/100")
        print(f"{'='*70}\n")

        print("--- EQUIPE ---\n")
        balanced, ratios = self.analyze_contribution_balance()
        for name, info in self.contributors.items():
            ratio = ratios.get(name, 0)
            print(f"  {name} ({info['email']})")
            print(f"    - {info['commits']} commits ({ratio}%)")
            print(f"    - {info['lines_added']} lignes ajoutees")
        print(f"\n  Equilibre: {'✓ Oui' if balanced else '✗ Non'}\n")

        print("--- DETAILS ---\n")
        for detail in self.details:
            print(f"  {detail}")

        return total_score, scores

    def generate_reports(self, final_score, scores):
        """Genere rapports JSON et HTML"""

        balanced, ratios = self.analyze_contribution_balance()

        report_data = {
            "iteration": self.iteration,
            "iteration_name": self.config["name"],
            "date": datetime.now().isoformat(),
            "score": final_score,
            "scores": scores,
            "contributors": [
                {
                    "name": name,
                    "email": info["email"],
                    "commits": info["commits"],
                    "lines_added": info["lines_added"],
                    "ratio": ratios.get(name, 0),
                }
                for name, info in self.contributors.items()
            ],
            "contribution_balanced": balanced,
            "details": self.details,
        }

        filename_json = f"evaluation_iteration_{self.iteration}.json"
        filename_html = f"evaluation_iteration_{self.iteration}.html"

        with open(filename_json, "w") as f:
            json.dump(report_data, f, indent=2)

        html = self._generate_html(report_data)
        with open(filename_html, "w") as f:
            f.write(html)

        print(f"\n✓ Rapports generes: {filename_json}, {filename_html}")

    def _generate_html(self, data):
        """Genere rapport HTML"""
        score = data["score"]
        color = "green" if score >= 70 else "orange" if score >= 50 else "red"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Evaluation Iteration {data['iteration']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }}
        h1 {{ margin: 0; font-size: 32px; }}
        .iteration {{ opacity: 0.9; margin-top: 10px; }}
        .score {{ font-size: 64px; font-weight: bold; color: {color}; text-align: center; margin: 30px 0; }}
        .section {{ background: white; padding: 25px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .criteria {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .criterion {{ padding: 15px; background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px; }}
        .criterion-name {{ font-weight: bold; color: #333; }}
        .criterion-score {{ font-size: 24px; color: #667eea; margin-top: 5px; }}
        .team {{ background: #e3f2fd; padding: 20px; border-radius: 8px; }}
        .contributor {{ margin: 15px 0; padding: 15px; background: white; border-radius: 4px; }}
        .contributor-name {{ font-weight: bold; font-size: 18px; color: #333; }}
        .contributor-stats {{ color: #666; margin-top: 8px; }}
        .details {{ margin-top: 20px; }}
        .detail-item {{ padding: 10px; margin: 8px 0; border-left: 3px solid #ddd; }}
        .success {{ border-color: green; background: #f1f9f1; }}
        .warning {{ border-color: orange; background: #fff8e1; }}
        .error {{ border-color: red; background: #ffebee; }}
        .balanced {{ display: inline-block; padding: 5px 15px; background: #4caf50; color: white; border-radius: 20px; margin-top: 10px; }}
        .unbalanced {{ display: inline-block; padding: 5px 15px; background: #ff9800; color: white; border-radius: 20px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Iteration {data['iteration']}: {data['iteration_name']}</h1>
        <div class="iteration">Evaluation du {data['date'][:10]}</div>
    </div>
    
    <div class="score">{score:.1f}/100</div>
    
    <div class="section">
        <h2>Resultats par Critere</h2>
        <div class="criteria">
"""

        criteria_names = {
            "functionality": "Fonctionnalite",
            "tests": "Tests",
            "quality": "Qualite Code",
            "git": "Git/Commits",
        }

        for key, name in criteria_names.items():
            weight = self.config[key]["weight"]
            score_val = data["scores"][key]
            html += f"""
            <div class="criterion">
                <div class="criterion-name">{name}</div>
                <div class="criterion-score">{score_val:.1f}/{weight}</div>
            </div>
"""

        html += """
        </div>
    </div>
    
    <div class="section team">
        <h2>Equipe</h2>
"""

        for contrib in data["contributors"]:
            html += f"""
        <div class="contributor">
            <div class="contributor-name">{contrib['name']}</div>
            <div class="contributor-stats">
                Email: {contrib['email']}<br>
                Commits: {contrib['commits']} ({contrib['ratio']:.1f}%)<br>
                Lignes ajoutees: {contrib['lines_added']}
            </div>
        </div>
"""

        balance_class = "balanced" if data["contribution_balanced"] else "unbalanced"
        balance_text = (
            "Equilibree" if data["contribution_balanced"] else "Desequilibree"
        )
        html += f'        <span class="{balance_class}">Contribution: {balance_text}</span>\n'

        html += """
    </div>
    
    <div class="section">
        <h2>Details</h2>
        <div class="details">
"""

        for detail in data["details"]:
            css_class = (
                "success" if "✓" in detail else "warning" if "⚠" in detail else "error"
            )
            html += f'            <div class="detail-item {css_class}">{detail}</div>\n'

        html += """
        </div>
    </div>
</body>
</html>"""

        return html


if __name__ == "__main__":
    evaluator = CodeEvaluator()
    final_score, scores = evaluator.run_evaluation()
    evaluator.generate_reports(final_score, scores)

    exit(0 if final_score >= 50 else 1)

    def evaluate_functionality(self):
        """Verifie que l'application demarre et repond"""
        points = 0
        max_points = 25

        # Test lancement app (simulation rapide)
        try:
            result = subprocess.run(
                ["python", "-c", 'import app; print("OK")'],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                points += 15
                self.details.append("✓ Application demarre sans erreur (15/15)")
            else:
                self.details.append("✗ Application ne demarre pas (0/15)")
        except Exception as e:
            self.details.append(f"✗ Erreur lancement: {e} (0/15)")

        # Test API data endpoint
        if os.path.exists("app.py"):
            with open("app.py", "r") as f:
                content = f.read()
                if (
                    '@app.get("/api/data")' in content
                    or "@app.get('/api/data')" in content
                ):
                    points += 10
                    self.details.append("✓ Endpoint /api/data present (10/10)")
                else:
                    self.details.append("✗ Endpoint /api/data manquant (0/10)")

        self.criteria["functionality"]["score"] = (points / max_points) * self.criteria[
            "functionality"
        ]["weight"]
        return points, max_points

    def evaluate_tests(self):
        """Evalue tests et couverture"""
        points = 0
        max_points = 20

        # Tests present et passent
        if os.path.exists("tests"):
            try:
                result = subprocess.run(
                    ["pytest", "tests/", "-v"], capture_output=True, timeout=60
                )
                if result.returncode == 0:
                    points += 10
                    self.details.append("✓ Tests passent (10/10)")
                else:
                    points += 5
                    self.details.append("⚠ Tests echouent partiellement (5/10)")
            except:
                self.details.append("✗ Erreur execution tests (0/10)")
        else:
            self.details.append("✗ Repertoire tests/ absent (0/10)")

        # Couverture
        if os.path.exists("coverage.xml"):
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse("coverage.xml")
                coverage = float(tree.getroot().attrib.get("line-rate", 0)) * 100

                if coverage >= 70:
                    points += 10
                    self.details.append(f"✓ Couverture {coverage:.1f}% >= 70% (10/10)")
                elif coverage >= 50:
                    points += 7
                    self.details.append(f"⚠ Couverture {coverage:.1f}% (7/10)")
                else:
                    points += 3
                    self.details.append(f"✗ Couverture {coverage:.1f}% < 50% (3/10)")
            except:
                self.details.append("✗ Erreur lecture couverture (0/10)")
        else:
            self.details.append("✗ Rapport couverture absent (0/10)")

        self.criteria["tests"]["score"] = (points / max_points) * self.criteria[
            "tests"
        ]["weight"]
        return points, max_points

    def evaluate_quality(self):
        """Evalue qualite code (lint, complexite)"""
        points = 0
        max_points = 20

        # Flake8
        if os.path.exists("flake8_report.json"):
            try:
                with open("flake8_report.json", "r") as f:
                    errors = json.load(f)
                    total_errors = sum(len(v) for v in errors.values())

                    if total_errors == 0:
                        points += 10
                        self.details.append("✓ Flake8: 0 erreur (10/10)")
                    elif total_errors <= 10:
                        points += 7
                        self.details.append(f"⚠ Flake8: {total_errors} erreurs (7/10)")
                    else:
                        points += 3
                        self.details.append(f"✗ Flake8: {total_errors} erreurs (3/10)")
            except:
                points += 5
                self.details.append("⚠ Erreur lecture flake8 (5/10)")

        # Complexite
        if os.path.exists("complexity_report.json"):
            try:
                with open("complexity_report.json", "r") as f:
                    data = json.load(f)
                    high_complexity = sum(
                        1
                        for file_data in data.values()
                        for func in file_data
                        if func.get("complexity", 0) > 10
                    )

                    if high_complexity == 0:
                        points += 10
                        self.details.append("✓ Complexite acceptable (10/10)")
                    elif high_complexity <= 3:
                        points += 6
                        self.details.append(
                            f"⚠ {high_complexity} fonctions complexes (6/10)"
                        )
                    else:
                        points += 2
                        self.details.append(
                            f"✗ {high_complexity} fonctions complexes (2/10)"
                        )
            except:
                points += 5
                self.details.append("⚠ Erreur lecture complexite (5/10)")

        self.criteria["quality"]["score"] = (points / max_points) * self.criteria[
            "quality"
        ]["weight"]
        return points, max_points

    def evaluate_poo_solid(self):
        """Evalue POO et principes SOLID"""
        points = 0
        max_points = 25

        classes_found = []
        expected_classes = ["Device", "Room", "Sensor", "Database"]

        # Analyser fichiers Python
        for py_file in Path(".").rglob("*.py"):
            if "venv" in str(py_file) or "test" in str(py_file):
                continue

            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes_found.append(node.name)
            except:
                continue

        # Classes presentes
        num_classes = len(set(classes_found))
        if num_classes >= 5:
            points += 8
            self.details.append(f"✓ {num_classes} classes definies (8/8)")
        elif num_classes >= 3:
            points += 5
            self.details.append(f"⚠ {num_classes} classes definies (5/8)")
        else:
            points += 2
            self.details.append(f"✗ Seulement {num_classes} classes (2/8)")

        # SRP: methodes par classe
        avg_methods = self._analyze_class_methods()
        if avg_methods <= 10:
            points += 7
            self.details.append(f"✓ Moyenne {avg_methods:.1f} methodes/classe (7/7)")
        else:
            points += 3
            self.details.append(f"⚠ Moyenne {avg_methods:.1f} methodes/classe (3/7)")

        # Structure dossiers
        if os.path.exists("domain") or os.path.exists("application"):
            points += 5
            self.details.append("✓ Structure en couches presente (5/5)")
        else:
            self.details.append("✗ Structure en couches absente (0/5)")

        # Heritage/composition
        if self._has_inheritance():
            points += 5
            self.details.append("✓ Heritage/composition utilise (5/5)")
        else:
            points += 2
            self.details.append("⚠ Heritage/composition limite (2/5)")

        self.criteria["poo_solid"]["score"] = (points / max_points) * self.criteria[
            "poo_solid"
        ]["weight"]
        return points, max_points

    def evaluate_organization(self):
        """Evalue organisation du code"""
        points = 0
        max_points = 10

        # Structure dossiers
        expected_dirs = ["domain", "application", "infrastructure", "tests"]
        found_dirs = sum(1 for d in expected_dirs if os.path.exists(d))

        if found_dirs >= 3:
            points += 5
            self.details.append(f"✓ Structure dossiers ({found_dirs}/4 presents) (5/5)")
        elif found_dirs >= 2:
            points += 3
            self.details.append(f"⚠ Structure partielle ({found_dirs}/4) (3/5)")
        else:
            self.details.append(f"✗ Structure incomplete ({found_dirs}/4) (0/5)")

        # Taille fichiers
        large_files = []
        for py_file in Path(".").rglob("*.py"):
            if "venv" not in str(py_file):
                lines = len(open(py_file).readlines())
                if lines > 300:
                    large_files.append((py_file.name, lines))

        if not large_files:
            points += 3
            self.details.append("✓ Fichiers < 300 lignes (3/3)")
        else:
            points += 1
            self.details.append(f"⚠ {len(large_files)} fichiers > 300 lignes (1/3)")

        # Separation concerns
        if os.path.exists("app.py"):
            with open("app.py", "r") as f:
                if len(f.readlines()) < 200:
                    points += 2
                    self.details.append("✓ app.py bien structure (2/2)")
                else:
                    self.details.append("⚠ app.py volumineux (0/2)")

        self.criteria["organization"]["score"] = (points / max_points) * self.criteria[
            "organization"
        ]["weight"]
        return points, max_points

    def _analyze_class_methods(self):
        """Calcule moyenne methodes par classe"""
        class_methods = []

        for py_file in Path(".").rglob("*.py"):
            if "venv" in str(py_file) or "test" in str(py_file):
                continue

            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            methods = [
                                n for n in node.body if isinstance(n, ast.FunctionDef)
                            ]
                            class_methods.append(len(methods))
            except:
                continue

        return sum(class_methods) / len(class_methods) if class_methods else 0

    def _has_inheritance(self):
        """Verifie presence heritage"""
        for py_file in Path(".").rglob("*.py"):
            if "venv" in str(py_file):
                continue

            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and node.bases:
                            return True
            except:
                continue

        return False

    def run_evaluation(self):
        """Execute evaluation complete"""
        print("\n" + "=" * 70)
        print("EVALUATION AUTOMATIQUE - ITERATION POO")
        print("=" * 70 + "\n")

        self.evaluate_functionality()
        self.evaluate_tests()
        self.evaluate_quality()
        self.evaluate_poo_solid()
        self.evaluate_organization()

        # Calcul note finale
        total_score = sum(c["score"] for c in self.criteria.values())

        # Affichage
        print("\n--- RESULTATS PAR CRITERE ---\n")
        for name, data in self.criteria.items():
            print(f"{name.upper():20s}: {data['score']:.1f}/{data['weight']}")

        print(f"\n{'='*70}")
        print(f"NOTE FINALE: {total_score:.1f}/100")
        print(f"{'='*70}\n")

        print("--- DETAILS ---\n")
        for detail in self.details:
            print(f"  {detail}")

        return total_score

    def generate_reports(self, final_score):
        """Genere rapports JSON et HTML"""

        # JSON
        report_data = {
            "date": datetime.now().isoformat(),
            "score": final_score,
            "criteria": self.criteria,
            "details": self.details,
        }

        with open("evaluation_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        # HTML
        html = self._generate_html(report_data)
        with open("evaluation_report.html", "w") as f:
            f.write(html)

        print("\n✓ Rapports generes: evaluation_report.json, evaluation_report.html")

    def _generate_html(self, data):
        """Genere rapport HTML"""
        score = data["score"]
        color = "green" if score >= 70 else "orange" if score >= 50 else "red"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport Evaluation POO</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        .score {{ font-size: 48px; font-weight: bold; color: {color}; text-align: center; margin: 30px 0; }}
        .criteria {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .criterion {{ margin: 15px 0; padding: 10px; background: white; border-left: 4px solid #667eea; }}
        .details {{ margin-top: 30px; }}
        .detail-item {{ padding: 8px; margin: 5px 0; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>Rapport d'Evaluation - Iteration POO</h1>
    <p><strong>Date:</strong> {data['date']}</p>
    
    <div class="score">{score:.1f}/100</div>
    
    <div class="criteria">
        <h2>Resultats par Critere</h2>
"""

        for name, crit in data["criteria"].items():
            html += f"""
        <div class="criterion">
            <strong>{name.upper()}</strong>: {crit['score']:.1f}/{crit['weight']}
        </div>
"""

        html += """
    </div>
    
    <div class="details">
        <h2>Details</h2>
"""

        for detail in data["details"]:
            css_class = (
                "success" if "✓" in detail else "warning" if "⚠" in detail else "error"
            )
            html += f'        <div class="detail-item {css_class}">{detail}</div>\n'

        html += """
    </div>
</body>
</html>"""

        return html


if __name__ == "__main__":
    evaluator = CodeEvaluator()
    final_score = evaluator.run_evaluation()
    evaluator.generate_reports(final_score)

    # Code retour selon note
    exit(0 if final_score >= 50 else 1)

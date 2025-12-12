#!/usr/bin/env python3
"""
Script d'evaluation automatique pour iteration POO
"""

import json
import os
import ast
import subprocess
from pathlib import Path
from datetime import datetime


class CodeEvaluator:
    def __init__(self):
        self.score = 0
        self.max_score = 100
        self.details = []
        self.criteria = {
            'functionality': {'weight': 25, 'score': 0},
            'tests': {'weight': 20, 'score': 0},
            'quality': {'weight': 20, 'score': 0},
            'poo_solid': {'weight': 25, 'score': 0},
            'organization': {'weight': 10, 'score': 0}
        }
        
    def evaluate_functionality(self):
        """Verifie que l'application demarre et repond"""
        points = 0
        max_points = 25
        
        # Test lancement app (simulation rapide)
        try:
            result = subprocess.run(
                ['python', '-c', 'import app; print("OK")'],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                points += 15
                self.details.append("✓ Application demarre sans erreur (15/15)")
            else:
                self.details.append("✗ Application ne demarre pas (0/15)")
        except Exception as e:
            self.details.append(f"✗ Erreur lancement: {e} (0/15)")
        
        # Test API data endpoint
        if os.path.exists('app.py'):
            with open('app.py', 'r') as f:
                content = f.read()
                if '@app.get("/api/data")' in content or '@app.get(\'/api/data\')' in content:
                    points += 10
                    self.details.append("✓ Endpoint /api/data present (10/10)")
                else:
                    self.details.append("✗ Endpoint /api/data manquant (0/10)")
        
        self.criteria['functionality']['score'] = (points / max_points) * self.criteria['functionality']['weight']
        return points, max_points
    
    def evaluate_tests(self):
        """Evalue tests et couverture"""
        points = 0
        max_points = 20
        
        # Tests present et passent
        if os.path.exists('tests'):
            try:
                result = subprocess.run(
                    ['pytest', 'tests/', '-v'],
                    capture_output=True,
                    timeout=60
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
        if os.path.exists('coverage.xml'):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse('coverage.xml')
                coverage = float(tree.getroot().attrib.get('line-rate', 0)) * 100
                
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
        
        self.criteria['tests']['score'] = (points / max_points) * self.criteria['tests']['weight']
        return points, max_points
    
    def evaluate_quality(self):
        """Evalue qualite code (lint, complexite)"""
        points = 0
        max_points = 20
        
        # Flake8
        if os.path.exists('flake8_report.json'):
            try:
                with open('flake8_report.json', 'r') as f:
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
        if os.path.exists('complexity_report.json'):
            try:
                with open('complexity_report.json', 'r') as f:
                    data = json.load(f)
                    high_complexity = sum(
                        1 for file_data in data.values()
                        for func in file_data
                        if func.get('complexity', 0) > 10
                    )
                    
                    if high_complexity == 0:
                        points += 10
                        self.details.append("✓ Complexite acceptable (10/10)")
                    elif high_complexity <= 3:
                        points += 6
                        self.details.append(f"⚠ {high_complexity} fonctions complexes (6/10)")
                    else:
                        points += 2
                        self.details.append(f"✗ {high_complexity} fonctions complexes (2/10)")
            except:
                points += 5
                self.details.append("⚠ Erreur lecture complexite (5/10)")
        
        self.criteria['quality']['score'] = (points / max_points) * self.criteria['quality']['weight']
        return points, max_points
    
    def evaluate_poo_solid(self):
        """Evalue POO et principes SOLID"""
        points = 0
        max_points = 25
        
        classes_found = []
        expected_classes = ['Device', 'Room', 'Sensor', 'Database']
        
        # Analyser fichiers Python
        for py_file in Path('.').rglob('*.py'):
            if 'venv' in str(py_file) or 'test' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
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
        if os.path.exists('domain') or os.path.exists('application'):
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
        
        self.criteria['poo_solid']['score'] = (points / max_points) * self.criteria['poo_solid']['weight']
        return points, max_points
    
    def evaluate_organization(self):
        """Evalue organisation du code"""
        points = 0
        max_points = 10
        
        # Structure dossiers
        expected_dirs = ['domain', 'application', 'infrastructure', 'tests']
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
        for py_file in Path('.').rglob('*.py'):
            if 'venv' not in str(py_file):
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
        if os.path.exists('app.py'):
            with open('app.py', 'r') as f:
                if len(f.readlines()) < 200:
                    points += 2
                    self.details.append("✓ app.py bien structure (2/2)")
                else:
                    self.details.append("⚠ app.py volumineux (0/2)")
        
        self.criteria['organization']['score'] = (points / max_points) * self.criteria['organization']['weight']
        return points, max_points
    
    def _analyze_class_methods(self):
        """Calcule moyenne methodes par classe"""
        class_methods = []
        
        for py_file in Path('.').rglob('*.py'):
            if 'venv' in str(py_file) or 'test' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                            class_methods.append(len(methods))
            except:
                continue
        
        return sum(class_methods) / len(class_methods) if class_methods else 0
    
    def _has_inheritance(self):
        """Verifie presence heritage"""
        for py_file in Path('.').rglob('*.py'):
            if 'venv' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and node.bases:
                            return True
            except:
                continue
        
        return False
    
    def run_evaluation(self):
        """Execute evaluation complete"""
        print("\n" + "="*70)
        print("EVALUATION AUTOMATIQUE - ITERATION POO")
        print("="*70 + "\n")
        
        self.evaluate_functionality()
        self.evaluate_tests()
        self.evaluate_quality()
        self.evaluate_poo_solid()
        self.evaluate_organization()
        
        # Calcul note finale
        total_score = sum(c['score'] for c in self.criteria.values())
        
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
            'date': datetime.now().isoformat(),
            'score': final_score,
            'criteria': self.criteria,
            'details': self.details
        }
        
        with open('evaluation_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # HTML
        html = self._generate_html(report_data)
        with open('evaluation_report.html', 'w') as f:
            f.write(html)
        
        print("\n✓ Rapports generes: evaluation_report.json, evaluation_report.html")
    
    def _generate_html(self, data):
        """Genere rapport HTML"""
        score = data['score']
        color = 'green' if score >= 70 else 'orange' if score >= 50 else 'red'
        
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
        
        for name, crit in data['criteria'].items():
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
        
        for detail in data['details']:
            css_class = 'success' if '✓' in detail else 'warning' if '⚠' in detail else 'error'
            html += f'        <div class="detail-item {css_class}">{detail}</div>\n'
        
        html += """
    </div>
</body>
</html>"""
        
        return html


if __name__ == '__main__':
    evaluator = CodeEvaluator()
    final_score = evaluator.run_evaluation()
    evaluator.generate_reports(final_score)
    
    # Code retour selon note
    exit(0 if final_score >= 50 else 1)

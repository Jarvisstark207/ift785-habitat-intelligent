# Guide Iterations

## Structure
```
ci/
└── iterations/
    ├── iteration_1.yml  (POO Basique)
    ├── iteration_2.yml  (Patterns)
    └── iteration_X.yml  (a creer)
```

## Format Config Iteration

```yaml
iteration: X
name: "Titre iteration"
description: "Description"

functionality:
  weight: 40
  checks:
    - name: "Verification"
      points: 15
      type: "import_test|class_detection|endpoint_check"
      # params specifiques selon type

tests:
  weight: 30
  min_coverage: 70
  min_tests: 5

quality:
  weight: 20
  max_flake8_errors: 10
  max_complexity: 10

git:
  weight: 10
  min_commits_per_person: 5
  min_contribution_ratio: 30
  conventional_commits_ratio: 60
```

## Nomenclature Branches

**Obligatoire :** `iteration_X` (ex: iteration_1, iteration_2, iteration_10)

Pipeline detecte automatiquement le numero et charge le bon YAML.

## Resultats

- **Logs:** Note finale immediate
- **Artifacts:** `evaluation_iteration_X.html` et `.json` (6 mois)
- **MR Comment:** Note + equipe + details

## Ajouter Iteration

1. Creer `ci/iterations/iteration_X.yml`
2. Push branche `iteration_X`
3. MR vers `main`
4. Pipeline s'execute automatiquement

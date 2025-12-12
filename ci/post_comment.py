#!/usr/bin/env python3
"""
Poste commentaire evaluation sur Merge Request GitLab
"""

import json
import os
import requests


def post_mr_comment():
    """Poste evaluation sur MR"""
    
    # Variables GitLab CI
    gitlab_url = os.getenv('CI_SERVER_URL', 'https://depot.dinf.usherbrooke.ca')
    project_id = os.getenv('CI_PROJECT_ID')
    mr_iid = os.getenv('CI_MERGE_REQUEST_IID')
    token = os.getenv('GITLAB_TOKEN')
    iteration = os.getenv('ITERATION', '1')
    
    if not all([project_id, mr_iid, token]):
        print("Variables GitLab manquantes, skip commentaire MR")
        return
    
    try:
        with open(f'evaluation_iteration_{iteration}.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Rapport evaluation introuvable")
        return
    
    score = data['score']
    emoji = '✅' if score >= 70 else '⚠️' if score >= 50 else '❌'
    
    comment = f"""## {emoji} Evaluation Iteration {data['iteration']}

**{data['iteration_name']}**

**Note Finale: {score:.1f}/100**

### Equipe
"""
    
    for contrib in data['contributors']:
        comment += f"- **{contrib['name']}** ({contrib['email']}): {contrib['commits']} commits ({contrib['ratio']:.1f}%)\n"
    
    balance = '✅ Equilibree' if data['contribution_balanced'] else '⚠️ Desequilibree'
    comment += f"\nContribution: {balance}\n"
    
    comment += "\n### Resultats par Critere\n\n"
    
    criteria_names = {
        'functionality': 'Fonctionnalite',
        'tests': 'Tests',
        'quality': 'Qualite Code',
        'git': 'Git/Commits'
    }
    
    for key, name in criteria_names.items():
        score_val = data['scores'][key]
        percentage = (score_val / data['scores'].get(key, 1)) * 100 if score_val > 0 else 0
        bar = '█' * int(percentage / 10) + '░' * (10 - int(percentage / 10))
        comment += f"- **{name}**: {score_val:.1f} {bar}\n"
    
    comment += "\n### Details (apercu)\n\n"
    
    for detail in data['details'][:8]:
        comment += f"- {detail}\n"
    
    if len(data['details']) > 8:
        comment += f"\n*... et {len(data['details']) - 8} autres details*\n"
    
    comment += f"\n📊 [Rapport HTML complet dans les artifacts]({gitlab_url}/{os.getenv('CI_PROJECT_PATH')}/-/jobs/{os.getenv('CI_JOB_ID')}/artifacts/browse)"
    
    api_url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
    headers = {'PRIVATE-TOKEN': token}
    payload = {'body': comment}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 201:
            print("Commentaire poste sur MR")
        else:
            print(f"Erreur API GitLab: {response.status_code}")
    except Exception as e:
        print(f"Erreur posting: {e}")


if __name__ == '__main__':
    post_mr_comment()


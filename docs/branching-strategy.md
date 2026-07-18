# Stratégie de branching NetOps — NexaCorp

## Branches permanentes
- `main`     : configuration en production sur les sites réels (protégée)
- `staging`  : configuration validée en lab, en attente de validation finale (protégée)
- `dev`      : branche d'intégration commune du groupe

## Branches temporaires
- `feature/<prenom>-jourX` : une branche par étudiant, par jour de formation
  Exemple : `feature/marie-jour2`, `feature/karim-jour3`

## Workflow quotidien (chaque étudiant, chaque jour)
1. Se synchroniser avec dev :
   git checkout dev
   git pull origin dev
2. Créer sa branche du jour :
   git checkout -b feature/<prenom>-jourX
3. Travailler, committer régulièrement sur cette branche
4. Pousser la branche :
   git push -u origin feature/<prenom>-jourX
5. Ouvrir une pull request feature/<prenom>-jourX → dev sur GitHub
6. Après revue (par le formateur ou un pair), merger dans dev

## Règle de promotion (fin de formation ou fin de jour selon décision du formateur)
1. Pull request dev → staging : déclenche les tests automatisés complets
2. Pull request staging → main : déclenche le déploiement en production (avec pre-checks/post-checks)

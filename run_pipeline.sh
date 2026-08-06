#!/bin/bash
set-e
echo "=================================================="
echo " ETAGE 1/5 : LINT"
echo "=================================================="
python3-m yamllint inventory/sites.yml inventory/network_model.yaml
echo "LINT OK"
echo
echo "=================================================="
echo " ETAGE 2/5 : VALIDATE (contrat YANG)"
echo "=================================================="
python3 scripts/yang_validate.py
echo
echo "=================================================="
echo " ETAGE 3/5 : TEST (pre-checks)"
echo "=================================================="
ansible-playbook playbooks/run_pre_checks.yml
echo
echo "=================================================="
echo " ETAGE 4/5 : DEPLOY (canary puis rolling)"
echo "=================================================="
ansible-playbook playbooks/deploy_zdd.yml
echo
echo "=================================================="
echo " ETAGE 5/5 : TEST (post-checks)"
echo "=================================================="
ansible-playbook playbooks/run_post_checks.yml
echo
echo "=================================================="
echo " PIPELINE COMPLET : SUCCES"
echo "=================================================="

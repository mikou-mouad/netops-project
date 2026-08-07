import os
import sys

from netops_client import VManageClient, VManageError

VMANAGE_URL = os.environ.get("VMANAGE_URL", "http://localhost:8000")
VMANAGE_USER = os.environ.get("VMANAGE_USER", "admin")
VMANAGE_PASS = os.environ.get("VMANAGE_PASS")

if not VMANAGE_PASS:
    print("ERREUR : variable d'environnement VMANAGE_PASS non definie.")
    sys.exit(1)

SITE_TOPOLOGY = [
    ("vedge-siege", 100, "mpls"),
    ("vedge-agence1", 101, "biz-internet"),
    ("vedge-agence2", 102, "biz-internet"),
]

POLICY_NAME = "Policy_QoS_Corp"
POLICY_RULES = [
    {"action": "set-priority-high", "sourceVN": "VN_CORP", "destVN": "VN_CORP"},
    {"action": "set-priority-low", "sourceVN": "VN_GUEST", "destVN": "VN_GUEST"},
]
TARGET_SITES = [100, 101, 102]


def main():
    client = VManageClient(base_url=VMANAGE_URL, username=VMANAGE_USER, password=VMANAGE_PASS)
    client.login()
    print("Authentifie sur vManage.\n")

    print("=== Verification/formation de la topologie SD-WAN ===")
    for device_id, site_id, tloc_color in SITE_TOPOLOGY:
        client.configure_site(device_id, site_id, tloc_color)
        print(f"  {device_id} -> site-id {site_id}, TLOC {tloc_color}")
    print()

    print(f"=== Deploiement de la policy centralisee '{POLICY_NAME}' ===")
    print(f"  Sites cibles : {TARGET_SITES}")
    for rule in POLICY_RULES:
        print(f"  Regle : {rule['sourceVN']} -> {rule['destVN']} : {rule['action']}")

    try:
        result = client.create_policy(POLICY_NAME, TARGET_SITES, POLICY_RULES)
    except VManageError as e:
        print(f"\n  ECHEC : {e}")
        sys.exit(1)

    policy_id, process_id = result["policyId"], result["processId"]
    print(f"\n  Policy creee : {policy_id}, activation en cours (tache {process_id})...")

    status = client.wait_for_action(process_id)
    print(f"  Statut final de l'activation : {status}\n")

    if status != "Success":
        print("ECHEC : la policy n'a pas ete activee correctement.")
        sys.exit(1)

    print("=== Verification finale ===")
    policies = client.list_policies()
    for p in policies:
        if p["policyId"] == policy_id:
            print(f"  {p['policyName']} : active = {p['active']}, sites = {p['targetSites']}")

    print("\nPolicy SD-WAN deployee et active avec succes sur tous les sites.")


if __name__ == "__main__":
    try:
        main()
    except VManageError as e:
        print(f"Erreur vManage : {e}")
        sys.exit(1)

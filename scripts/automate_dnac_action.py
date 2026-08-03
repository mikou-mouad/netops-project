import os
import sys

from netops_client import DNACClient, DNACError

DNAC_URL = os.environ.get("DNAC_URL", "http://localhost:6000")
DNAC_USER = os.environ.get("DNAC_USER", "admin")
DNAC_PASS = os.environ.get("DNAC_PASS")

if not DNAC_PASS:
    print("ERREUR : variable d'environnement DNAC_PASS non definie.")
    sys.exit(1)

TEMPLATE_ID = "tpl-vlan-invite-v1"


def main():
    client = DNACClient(base_url=DNAC_URL, username=DNAC_USER, password=DNAC_PASS)

    print(f"Authentification sur {DNAC_URL}...")
    client.authenticate()
    print("Authentification reussie.\n")

    devices = client.get_devices()
    print(f"{len(devices)} equipement(s) trouve(s) dans l'inventaire DNA Center :")
    for d in devices:
        print(f"  - {d['hostname']} ({d['managementIpAddress']}) : {d['reachabilityStatus']}")
    print()

    for device in devices:
        print(f"Deploiement du template '{TEMPLATE_ID}' sur {device['hostname']}...")
        task_id = client.deploy_template(
            template_id=TEMPLATE_ID,
            device_id=device["id"],
            params={"vlan_id": 99, "vlan_name": "GUEST"},
        )
        print(f"  Tache creee : {task_id}, attente de la fin du deploiement...")
        try:
            result = client.wait_for_task(task_id, max_attempts=6, delay=1)
            print(f"  -> {result['progress']}\n")
        except DNACError as e:
            print(f"  -> ECHEC : {e}\n")


if __name__ == "__main__":
    try:
        main()
    except DNACError as e:
        print(f"Erreur DNA Center : {e}")
        sys.exit(1)

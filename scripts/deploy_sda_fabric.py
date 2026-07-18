import os
import sys

from netops_client import SDAClient, DNACError

DNAC_URL = os.environ.get("DNAC_URL", "http://localhost:6000")
DNAC_USER = os.environ.get("DNAC_USER", "admin")
DNAC_PASS = os.environ.get("DNAC_PASS")

if not DNAC_PASS:
    print("ERREUR : variable d'environnement DNAC_PASS non definie.")
    sys.exit(1)

FABRIC_SITES = [
    ("Global/NexaCorp/Siege", "dev-siege"),
    ("Global/NexaCorp/Agence1", "dev-agence1"),
    ("Global/NexaCorp/Agence2", "dev-agence2"),
]

HOSTS_TO_ONBOARD = [
    ("dev-siege", "GigabitEthernet0/1", "VN_CORP"),
    ("dev-agence1", "GigabitEthernet0/1", "VN_CORP"),
    ("dev-agence2", "GigabitEthernet0/1", "VN_GUEST"),
]


def main():
    client = SDAClient(base_url=DNAC_URL, username=DNAC_USER, password=DNAC_PASS)
    client.authenticate()
    print("Authentifie sur DNA Center.\n")

    print("=== Creation des sites de la fabric SD-Access ===")
    for site_name, device_id in FABRIC_SITES:
        result = client.create_fabric_site(site_name, device_id)
        roles = "/".join(result["site"]["roles"])
        print(f"  {site_name} -> {device_id} ({roles})")
    print()

    print("=== Onboarding automatise des hotes ===")
    for device_id, interface, vn in HOSTS_TO_ONBOARD:
        try:
            result = client.onboard_host(device_id, interface, vn)
            info = result["onboarding"]
            print(f"  OK : {info['device']}/{info['interfaceName']} -> {info['virtualNetworkName']} ({info['ipPool']})")
        except DNACError as e:
            print(f"  ECHEC sur {device_id}/{interface} : {e}")
    print()

    print("=== Verification de la sante de la fabric ===")
    health = client.fabric_health()["response"]
    degraded = False
    for site in health:
        print(f"  {site['site']} : {site['status']}")
        for issue in site["issues"]:
            print(f"    -> {issue}")
            degraded = True

    if degraded:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except DNACError as e:
        print(f"Erreur : {e}")
        sys.exit(1)

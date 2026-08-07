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
    ("vedge-agence2", 102, "biz-internet")
]


def main():
    client = VManageClient(base_url=VMANAGE_URL, username=VMANAGE_USER, password=VMANAGE_PASS)
    client.login()
    print("Authentifie sur vManage.\n")

    devices = client.get_vedges()
    print(f"{len(devices)} vEdge(s) trouve(s) dans l'inventaire :")
    for d in devices:
        print(f"  - {d['host-name']} ({d['deviceId']}) : {d['reachability']}")
    print()

    print("=== Configuration de la topologie SD-WAN ===")
    for device_id, site_id, tloc_color in SITE_TOPOLOGY:
        client.configure_site(device_id, site_id, tloc_color)
        print(f"  {device_id} -> site-id {site_id}, TLOC {tloc_color}")
    print()

    print("=== Verification de l'overlay (sessions OMP) ===")
    all_up = True
    for d in devices:
        summary = client.omp_summary(d["deviceId"])
        print(f"  {d['host-name']} ({d['deviceId']}) : {summary['omp-peers-up']} pair(s) OMP actif(s), statut = {summary['status']}")
        if summary["status"] != "up":
            all_up = False

    if not all_up:
        print("\nATTENTION : au moins un site n'a pas etabli de session OMP avec le reste de l'overlay.")
        sys.exit(1)

    print("\nTopologie SD-WAN entierement formee (tous les sites se voient via OMP).")


if __name__ == "__main__":
    try:
        main()
    except VManageError as e:
        print(f"Erreur vManage : {e}")
        sys.exit(1)

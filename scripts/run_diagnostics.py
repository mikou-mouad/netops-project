import json
import os
import sys

import yaml

from netops_client import diagnose_site

HERE = os.path.dirname(os.path.abspath(__file__))
SITES_FILE = os.path.join(HERE, "..", "inventory", "sites.yml")
DIAG_DIR = os.path.join(HERE, "..", "diagnostics")

API_TOKEN = os.environ.get("VAULT_API_TOKEN")
if not API_TOKEN:
    print("ERREUR : variable d'environnement VAULT_API_TOKEN non definie.")
    print("Exemple : export VAULT_API_TOKEN=s3cr3t-token-nexacorp")
    sys.exit(1)


def main():
    with open(SITES_FILE) as f:
        sites = yaml.safe_load(f)["sites"]

    os.makedirs(DIAG_DIR, exist_ok=True)
    reports = []

    print(f"{'SITE':10s} {'JOIGNABLE':10s} {'LATENCE':10s} {'AUTH':6s} {'INTERFACES DOWN'}")
    print("-" * 70)

    for site in sites:
        base_url = f"http://localhost:{site['api_port']}"
        device_id = f"router-{site['nom']}-01"
        report = diagnose_site(site["nom"], base_url, API_TOKEN, device_id)
        reports.append(report)

        joignable = "oui" if report["reachable"] else "NON"
        latence = f"{report['latency_ms']} ms" if report["latency_ms"] else "-"
        auth = "ok" if report["auth_ok"] else ("NON" if report["auth_ok"] is False else "-")
        down = ", ".join(report["interfaces_down"]) if report["interfaces_down"] else "-"

        print(f"{site['nom']:10s} {joignable:10s} {latence:10s} {auth:6s} {down}")

    print()
    for report in reports:
        print(f"[{report['site']}] Actions suggerees :")
        for action in report["suggested_actions"]:
            print(f"  - {action}")

    timestamp = reports[0]["timestamp"].replace(":", "-")
    report_file = os.path.join(DIAG_DIR, f"diagnostic_{timestamp}.json")
    with open(report_file, "w") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    print(f"\nRapport complet ecrit dans {report_file}")

    if any(not r["reachable"] or r["auth_ok"] is False or r["interfaces_down"] for r in reports):
        sys.exit(1)


if __name__ == "__main__":
    main()

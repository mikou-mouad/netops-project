import os
import sys

from netops_client import APICClient, ACIError

APIC_URL = os.environ.get("APIC_URL", "http://localhost:7000")
APIC_USER = os.environ.get("APIC_USER", "admin")
APIC_PASS = os.environ.get("APIC_PASS")

if not APIC_PASS:
    print("ERREUR : variable d'environnement APIC_PASS non definie.")
    sys.exit(1)

TENANT_NAME = "NexaCorp_DC"

TENANT_TREE = {
    "fvTenant": {
        "attributes": {"name": TENANT_NAME},
        "children": [
            {"fvCtx": {"attributes": {"name": "NexaCorp_VRF"}}},
            {
                "fvBD": {
                    "attributes": {"name": "BD_Servers"},
                    "children": [
                        {"fvRsCtx": {"attributes": {"tnFvCtxName": "NexaCorp_VRF"}}}
                    ],
                }
            },
            {
                "vzBrCP": {
                    "attributes": {"name": "CT_App_to_DB"},
                    "children": [
                        {"vzSubj": {"attributes": {"name": "subj_app_db"}}}
                    ],
                }
            },
            {
                "fvAp": {
                    "attributes": {"name": "AP_ERP"},
                    "children": [
                        {
                            "fvAEPg": {
                                "attributes": {"name": "EPG_App"},
                                "children": [
                                    {"fvRsBd": {"attributes": {"tnFvBDName": "BD_Servers"}}},
                                    {"fvRsCons": {"attributes": {"tnVzBrCPName": "CT_App_to_DB"}}},
                                ],
                            }
                        },
                        {
                            "fvAEPg": {
                                "attributes": {"name": "EPG_DB"},
                                "children": [
                                    {"fvRsBd": {"attributes": {"tnFvBDName": "BD_Servers"}}},
                                    {"fvRsProv": {"attributes": {"tnVzBrCPName": "CT_App_to_DB"}}},
                                ],
                            }
                        },
                    ],
                }
            },
        ],
    }
}


def main():
    client = APICClient(base_url=APIC_URL, username=APIC_USER, password=APIC_PASS)
    client.login()
    print("Authentifie sur APIC.\n")

    print(f"Deploiement du tenant '{TENANT_NAME}' (VRF, bridge domain, AP, 2 EPG, contrat)...")
    client.deploy_tenant(TENANT_NAME, TENANT_TREE)
    print("Deploiement reussi.\n")

    print("Verification : relecture du tenant deploye...")
    tenant = client.get_tenant(TENANT_NAME)
    if tenant["imdata"]:
        print("  OK : le tenant est bien present sur APIC.\n")
    else:
        print("  ECHEC : le tenant n'a pas ete trouve.\n")
        sys.exit(1)

    print("Verification metier : EPG_App peut-il consommer les services d'EPG_DB ?")
    result = client.check_contract(TENANT_NAME, consumer_epg="EPG_App", provider_epg="EPG_DB")
    if result.get("allowed"):
        print(f"  OK : autorise via le contrat '{result['contract']}'.\n")
    else:
        print(f"  REFUSE : {result.get('reason')}\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except ACIError as e:
        print(f"Erreur ACI : {e}")
        sys.exit(1)

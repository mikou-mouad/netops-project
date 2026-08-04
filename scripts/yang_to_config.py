"""
Transforme une instance de donnees (inventory/network_model.yaml), conforme
a la structure definie par yang/nexacorp-interfaces.yang, en fichiers
host_vars Ansible exploitables (un fichier par site).
"""
import os
import sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(HERE, "..", "inventory", "network_model.yaml")
HOST_VARS_DIR = os.path.join(HERE, "..", "inventory", "host_vars")

ALLOWED_STATES = {"up", "down"}


class YangValidationError(Exception):
    """Erreur levee quand une instance ne respecte pas le modele YANG."""
    pass


def validate_interface(site, iface):
    if "name" not in iface or not isinstance(iface["name"], str):
        raise YangValidationError(f"[{site}] 'name' manquant ou invalide : {iface}")

    if "vlan-id" not in iface:
        raise YangValidationError(f"[{site}] 'vlan-id' obligatoire manquant pour {iface.get('name')}")
    vlan_id = iface["vlan-id"]
    if not isinstance(vlan_id, int) or not (1 <= vlan_id <= 4094):
        raise YangValidationError(f"[{site}] vlan-id hors plage (1-4094) pour {iface.get('name')} : {vlan_id}")

    enabled = iface.get("enabled", "up")
    if enabled not in ALLOWED_STATES:
        raise YangValidationError(f"[{site}] 'enabled' doit etre 'up' ou 'down' pour {iface.get('name')} : {enabled}")


def main():
    with open(MODEL_FILE) as f:
        data = yaml.safe_load(f)

    os.makedirs(HOST_VARS_DIR, exist_ok=True)

    for site, site_data in data["sites"].items():
        interfaces = site_data["interfaces"]

        for iface in interfaces:
            validate_interface(site, iface)

        host_vars = {"interfaces": interfaces}
        out_path = os.path.join(HOST_VARS_DIR, f"{site}.yml")
        with open(out_path, "w") as f:
            f.write("---\n")
            yaml.dump(host_vars, f, default_flow_style=False, sort_keys=False)

        print(f"OK : {len(interfaces)} interface(s) validees et ecrites dans {out_path}")


if __name__ == "__main__":
    try:
        main()
    except YangValidationError as e:
        print(f"ERREUR de validation YANG : {e}", file=sys.stderr)
        sys.exit(1)

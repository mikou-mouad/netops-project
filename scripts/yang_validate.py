"""Etage VALIDATE du pipeline : valide chaque site de network_model.yaml
contre le modele YANG (yangson), un site a la fois, puis ecrit un
host_vars/<site>.yml par site valide."""
import os
import sys

import yaml
from yangson import DataModel
from yangson.exceptions import YangsonException

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(HERE, "..", "inventory", "network_model.yaml")
LIBRARY_FILE = os.path.join(HERE, "..", "yang", "yang-library.json")
MODULE_DIR = [os.path.join(HERE, "..", "yang")]
HOST_VARS_DIR = os.path.join(HERE, "..", "inventory", "host_vars")


def main():
    dm = DataModel.from_file(LIBRARY_FILE, MODULE_DIR)

    with open(MODEL_FILE) as f:
        data = yaml.safe_load(f)

    os.makedirs(HOST_VARS_DIR, exist_ok=True)
    for site_name, site_data in data["sites"].items():
        raw = {"nexacorp-interfaces:interface": site_data["interfaces"]}
        instance = dm.from_raw(raw)
        try:
            instance.validate()
        except YangsonException as e:
            print(f"VALIDATION ECHOUEE [{site_name}] : {e}")
            sys.exit(1)

        host_vars_path = os.path.join(HOST_VARS_DIR, f"{site_name}.yml")
        with open(host_vars_path, "w") as f:
            yaml.safe_dump({"interfaces": site_data["interfaces"]}, f, allow_unicode=True)
        print(f"OK [{site_name}] : {len(site_data['interfaces'])} interface(s) validees")

    print(f"\nVALIDATION OK : {len(data['sites'])} site(s) conformes au modele YANG.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
Inventaire dynamique NetOps NexaCorp.
Lit inventory/sites.yml et genere un inventaire Ansible JSON.
"""
import json
import os
import sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SITES_FILE = os.path.join(HERE, "sites.yml")


def build_inventory():
    with open(SITES_FILE) as f:
        data = yaml.safe_load(f)

    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"children": ["hub", "spokes"]},
        "hub": {"hosts": []},
        "spokes": {"hosts": []},
    }

    for site in data["sites"]:
        name = site["nom"]
        group = "hub" if site["role"] == "hub" else "spokes"
        inventory[group]["hosts"].append(name)
        inventory["_meta"]["hostvars"][name] = {
            "ansible_connection": "local",
            "ansible_python_interpreter": sys.executable,
            "api_url": f"http://localhost:{site['api_port']}",
            "site_role": site["role"],
        }
    return inventory


def main():

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print(json.dumps(build_inventory()))
    elif len(sys.argv) > 2 and sys.argv[1] == "--host":
        print(json.dumps({}))
    else:
        print("Usage:--list ou--host <nom>", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

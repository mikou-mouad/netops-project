import glob
import os
import re
import sys

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "generated_configs")


def split_interfaces(config_text):
    """Retourne une liste de (nom_interface, bloc_texte) pour chaque interface."""
    blocks = re.split(r"\n(?=interface )", config_text)
    interfaces = []
    for block in blocks:
        match = re.match(r"interface (\S+)", block)
        if match:
            interfaces.append((match.group(1), block))
    return interfaces


def analyze_config(config_text, filename):
    issues = []

    if "no ip domain-lookup" not in config_text:
        issues.append({
            "file": filename,
            "scope": "global",
            "issue": "'no ip domain-lookup' absent",
            "impact": "Une faute de frappe en mode exec declenche une resolution DNS de ~9 secondes avant de rendre la main",
            "fix": "no ip domain-lookup",
        })

    for iface_name, block in split_interfaces(config_text):
        is_active = "no shutdown" in block
        if not is_active:
            continue

        if "duplex" not in block or "speed" not in block:
            issues.append({
                "file": filename,
                "scope": iface_name,
                "issue": "duplex/speed non explicites sur une interface active",
                "impact": "L'auto-negociation peut aboutir a un mauvais appairage (duplex mismatch), source classique de collisions et de degradation de performance",
                "fix": "duplex full / speed 1000 (ou valeurs adaptees au lien)",
            })

        if "switchport access vlan" in block and "spanning-tree portfast" not in block:
            issues.append({
                "file": filename,
                "scope": iface_name,
                "issue": "spanning-tree portfast absent sur un port d'acces actif",
                "impact": "Le port passe par les etats blocking/listening/learning de STP (jusqu'a 30-50s) avant de transmettre, ralentissant le demarrage des hotes connectes",
                "fix": "spanning-tree portfast",
            })

    return issues


def main():
    files = sorted(glob.glob(os.path.join(CONFIG_DIR, "*.cfg")))
    if not files:
        print(f"Aucun fichier de configuration trouve dans {CONFIG_DIR}")
        sys.exit(1)

    total_issues = 0
    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath) as f:
            content = f.read()

        issues = analyze_config(content, filename)
        total_issues += len(issues)

        print(f"=== {filename} ===")
        if not issues:
            print("  Aucun probleme d'optimisation detecte.\n")
            continue

        for issue in issues:
            print(f"  [{issue['scope']}] {issue['issue']}")
            print(f"    Impact : {issue['impact']}")
            print(f"    Correction suggeree : {issue['fix']}")
        print()

    print(f"Bilan : {total_issues} probleme(s) d'optimisation detecte(s) sur {len(files)} fichier(s).")
    if total_issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

import datetime

from .client import NetworkClient
from .exceptions import NetworkAPIError
from .logger_config import setup_logger

logger = setup_logger(__name__)


def diagnose_site(site_name, base_url, api_token, device_id):
    """Execute un diagnostic complet d'un site et retourne un rapport structure."""
    report = {
        "site": site_name,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "reachable": False,
        "latency_ms": None,
        "auth_ok": None,
        "interfaces_down": [],
        "suggested_actions": [],
    }

    client = NetworkClient(base_url=base_url, api_token=api_token)

    # Etape 1 : le site est-il joignable ?
    try:
        health = client.get_health()
        report["reachable"] = True
        report["latency_ms"] = health["elapsed_ms"]
        logger.info(f"{site_name} : joignable ({health['elapsed_ms']} ms)")
    except NetworkAPIError as e:
        report["suggested_actions"].append(
            "Site injoignable : verifier que le conteneur/service tourne, verifier le reseau/port"
        )
        logger.error(f"{site_name} : injoignable ({e})")
        return report

    if report["latency_ms"] and report["latency_ms"] > 200:
        report["suggested_actions"].append(
            f"Latence elevee ({report['latency_ms']} ms) : verifier la charge du site ou le reseau"
        )

    # Etape 2 : l'authentification et les interfaces
    try:
        down = client.count_interfaces_down(device_id)
        report["auth_ok"] = True
        report["interfaces_down"] = down
        if down:
            report["suggested_actions"].append(
                f"Interface(s) en panne : {down} -> verifier le cablage ou la configuration"
            )
    except NetworkAPIError as e:
        report["auth_ok"] = False
        if "Authentification" in str(e):
            report["suggested_actions"].append(
                "Authentification refusee : verifier que le token Ansible Vault correspond "
                "a celui configure sur le site (variable API_TOKEN)"
            )
        else:
            report["suggested_actions"].append(f"Erreur lors de la lecture des interfaces : {e}")
        logger.error(f"{site_name} : {e}")

    if not report["suggested_actions"]:
        report["suggested_actions"].append("Aucune anomalie detectee")

    return report

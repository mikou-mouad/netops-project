import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scripts/logs_network_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("network_client")


class NetworkAPIError(Exception):
    """Erreur levee lorsque l'API reseau repond en erreur."""
    pass


class NetworkClient:
    """Client modulaire pour interroger une API reseau REST."""

    def __init__(self, base_url, timeout=5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_interfaces(self, device_id):
        url = f"{self.base_url}/api/devices/{device_id}/interfaces"
        logger.info(f"Requete GET vers {url}")
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Echec de la requete API : {e}")
            raise NetworkAPIError(f"Impossible de contacter l'API : {e}")

        data = response.json()
        logger.info(f"Reponse recue pour {device_id} : {len(data['interfaces'])} interfaces")
        return data["interfaces"]

    def count_interfaces_down(self, device_id):
        interfaces = self.get_interfaces(device_id)
        down = [name for name, info in interfaces.items() if info["status"] == "down"]
        if down:
            logger.warning(f"Interfaces down sur {device_id} : {down}")
        return down


if __name__ == "__main__":
    client = NetworkClient(base_url="http://localhost:5000")

    interfaces = client.get_interfaces("router-siege-01")
    for name, info in interfaces.items():
        print(f"{name} : {info['status']} (ip={info['ip']}, vlan={info['vlan']})")

    down = client.count_interfaces_down("router-siege-01")
    print(f"\nInterfaces en panne : {down if down else 'aucune'}")

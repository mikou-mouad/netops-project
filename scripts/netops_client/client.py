import requests

from .exceptions import NetworkAPIError
from .logger_config import setup_logger

logger = setup_logger(__name__)

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
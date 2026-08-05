import time

import requests

from .exceptions import NetworkAPIError
from .logger_config import setup_logger

logger = setup_logger(__name__)


class NetworkClient:
    """Client modulaire pour interroger une API reseau REST."""

    def __init__(self, base_url, api_token=None, timeout=5):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout

    def _headers(self):
        if self.api_token:
            return {"X-Api-Token": self.api_token}
        return {}

    def get_health(self):
        url = f"{self.base_url}/health"
        start = time.monotonic()
        try:
            response = requests.get(url, timeout=self.timeout)
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Echec du health check : {e}")
            raise NetworkAPIError(f"Site injoignable : {e}")

        return {"data": response.json(), "elapsed_ms": elapsed_ms}

    def get_interfaces(self, device_id):
        url = f"{self.base_url}/api/devices/{device_id}/interfaces"
        logger.info(f"Requete GET vers {url}")
        try:
            response = requests.get(url, headers=self._headers(), timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 401:
                logger.error(f"Authentification refusee sur {url}")
                raise NetworkAPIError("Authentification refusee (token invalide ou manquant)")
            logger.error(f"Erreur HTTP {status} sur {url}")
            raise NetworkAPIError(f"Erreur HTTP {status} : {e}")
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

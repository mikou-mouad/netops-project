import time

import requests


class DNACError(Exception):
    """Erreur levee lors d'un echange avec l'API DNA Center."""
    pass


class DNACClient:
    """Client minimal pour l'API Cisco DNA Center (authentification, inventaire, deploiement de template)."""

    def __init__(self, base_url, username, password, timeout=5):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.token = None

    def authenticate(self):
        url = f"{self.base_url}/dna/system/api/v1/auth/token"
        response = requests.post(url, auth=(self.username, self.password), timeout=self.timeout)
        if response.status_code != 200:
            raise DNACError(f"Authentification refusee ({response.status_code})")
        self.token = response.json()["Token"]
        return self.token

    def _headers(self):
        if not self.token:
            raise DNACError("Non authentifie : appelez authenticate() d'abord")
        return {"X-Auth-Token": self.token}

    def get_devices(self):
        url = f"{self.base_url}/dna/intent/api/v1/network-device"
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        if response.status_code != 200:
            raise DNACError(f"Erreur inventaire ({response.status_code}) : {response.text}")
        return response.json()["response"]

    def deploy_template(self, template_id, device_id, params=None):
        url = f"{self.base_url}/dna/intent/api/v1/template-programmer/template/deploy"
        body = {
            "templateId": template_id,
            "targetInfo": [{"id": device_id, "type": "MANAGED_DEVICE_UUID", "params": params or {}}],
        }
        response = requests.post(url, headers=self._headers(), json=body, timeout=self.timeout)
        if response.status_code != 200:
            raise DNACError(f"Echec du declenchement du deploiement : {response.text}")
        return response.json()["taskId"]

    def wait_for_task(self, task_id, max_attempts=10, delay=1):
        url = f"{self.base_url}/dna/intent/api/v1/task/{task_id}"
        for attempt in range(1, max_attempts + 1):
            response = requests.get(url, headers=self._headers(), timeout=self.timeout)
            if response.status_code != 200:
                raise DNACError(f"Erreur lors du suivi de la tache : {response.text}")
            data = response.json()["response"]
            if data.get("isError"):
                raise DNACError(f"Tache en erreur : {data}")
            if data["progress"] != "IN_PROGRESS":
                return data
            time.sleep(delay)
        raise DNACError(f"Tache {task_id} toujours en cours apres {max_attempts} tentatives")

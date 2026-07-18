import requests


class VManageError(Exception):
    """Erreur levee lors d'un echange avec l'API vManage (SD-WAN)."""
    pass


class VManageClient:
    """Client minimal pour l'API Cisco SD-WAN vManage : authentification par session + jeton XSRF."""

    def __init__(self, base_url, username, password, timeout=5):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self.xsrf_token = None

    def login(self):
        url = f"{self.base_url}/j_security_check"
        response = self.session.post(
            url,
            data={"j_username": self.username, "j_password": self.password},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise VManageError(f"Authentification refusee ({response.status_code})")

        token_response = self.session.get(f"{self.base_url}/dataservice/client/token", timeout=self.timeout)
        if token_response.status_code != 200:
            raise VManageError("Impossible de recuperer le jeton XSRF")
        self.xsrf_token = token_response.text

    def _headers(self):
        if not self.xsrf_token:
            raise VManageError("Non authentifie : appelez login() d'abord")
        return {"X-XSRF-TOKEN": self.xsrf_token}

    def get_vedges(self):
        url = f"{self.base_url}/dataservice/system/device/vedges"
        response = self.session.get(url, headers=self._headers(), timeout=self.timeout)
        if response.status_code != 200:
            raise VManageError(f"Erreur inventaire vEdges : {response.text}")
        return response.json()["data"]

    def configure_site(self, device_id, site_id, tloc_color):
        url = f"{self.base_url}/dataservice/system/device/site"
        body = {"deviceId": device_id, "siteId": site_id, "tlocColor": tloc_color}
        response = self.session.post(url, headers=self._headers(), json=body, timeout=self.timeout)
        if response.status_code != 200:
            raise VManageError(f"Echec de la configuration du site : {response.text}")
        return response.json()

    def omp_summary(self, device_id):
        url = f"{self.base_url}/dataservice/device/omp/summary"
        response = self.session.get(url, headers=self._headers(), params={"deviceId": device_id}, timeout=self.timeout)
        if response.status_code != 200:
            raise VManageError(f"Erreur OMP summary : {response.text}")
        return response.json()["data"]

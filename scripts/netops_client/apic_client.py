import requests


class ACIError(Exception):
    """Erreur levee lors d'un echange avec l'API APIC (Cisco ACI)."""
    pass


class APICClient:
    """Client minimal pour l'API Cisco ACI (APIC) : authentification et deploiement de tenant."""

    def __init__(self, base_url, username, password, timeout=5):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.token = None

    def login(self):
        url = f"{self.base_url}/api/aaaLogin.json"
        body = {"aaaUser": {"attributes": {"name": self.username, "pwd": self.password}}}
        response = requests.post(url, json=body, timeout=self.timeout)
        if response.status_code != 200:
            raise ACIError(f"Authentification refusee ({response.status_code})")
        self.token = response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
        return self.token

    def _headers(self):
        if not self.token:
            raise ACIError("Non authentifie : appelez login() d'abord")
        return {"APIC-Cookie": self.token}

    def deploy_tenant(self, tenant_name, tenant_tree):
        url = f"{self.base_url}/api/mo/uni/tn-{tenant_name}.json"
        response = requests.post(url, headers=self._headers(), json=tenant_tree, timeout=self.timeout)
        if response.status_code != 200:
            raise ACIError(f"Echec du deploiement du tenant : {response.text}")
        return response.json()

    def get_tenant(self, tenant_name):
        url = f"{self.base_url}/api/mo/uni/tn-{tenant_name}.json"
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        if response.status_code != 200:
            raise ACIError(f"Tenant introuvable : {response.text}")
        return response.json()

    def check_contract(self, tenant_name, consumer_epg, provider_epg):
        url = f"{self.base_url}/api/mo/uni/tn-{tenant_name}/contract-check.json"
        response = requests.get(
            url, headers=self._headers(), params={"consumer": consumer_epg, "provider": provider_epg}, timeout=self.timeout
        )
        return response.json()

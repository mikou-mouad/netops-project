from .dnac_client import DNACClient, DNACError


class SDAClient(DNACClient):
    """Client SD-Access, etend le client DNA Center avec les operations de fabric."""

    def create_fabric_site(self, site_name_hierarchy, device_id):
        url = f"{self.base_url}/dna/intent/api/v1/business/sda/fabric-site"
        return self._post(url, {"siteNameHierarchy": site_name_hierarchy, "deviceId": device_id})

    def list_fabric_sites(self):
        url = f"{self.base_url}/dna/intent/api/v1/business/sda/fabric-site"
        return self._get(url)

    def onboard_host(self, device_id, interface_name, virtual_network_name):
        url = f"{self.base_url}/dna/intent/api/v1/business/sda/hostonboarding/user-device"
        body = {
            "deviceId": device_id,
            "interfaceName": interface_name,
            "virtualNetworkName": virtual_network_name,
        }
        return self._post(url, body)

    def fabric_health(self):
        url = f"{self.base_url}/dna/intent/api/v1/business/sda/fabric-site/health"
        return self._get(url)

    def _post(self, url, body):
        import requests
        response = requests.post(url, headers=self._headers(), json=body, timeout=self.timeout)
        if response.status_code not in (200,):
            raise DNACError(response.json().get("error", response.text))
        return response.json()

    def _get(self, url):
        import requests
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        if response.status_code != 200:
            raise DNACError(response.json().get("error", response.text))
        return response.json()

from netops_client import NetworkClient, NetworkAPIError

SITES = {
    "siege": "http://localhost:5001",
    "agence1": "http://localhost:5002",
    "agence2": "http://localhost:5003",
}

if __name__ == "__main__":
    for site, url in SITES.items():
        client = NetworkClient(base_url=url)
        try:
            down = client.count_interfaces_down(f"router-{site}-01")
            statut = "OK" if not down else f"ATTENTION : {down}"
            print(f"{site:10s} -> {statut}")
        except NetworkAPIError as e:
            print(f"{site:10s} -> INJOIGNABLE ({e})")

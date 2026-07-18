from netops_client import NetworkClient, NetworkAPIError

if __name__ == "__main__":
    client = NetworkClient(base_url="http://localhost:5000")

    try:
        interfaces = client.get_interfaces("router-siege-01")
        for name, info in interfaces.items():
            print(f"{name} : {info['status']} (ip={info['ip']}, vlan={info['vlan']})")

        down = client.count_interfaces_down("router-siege-01")
        print(f"\nInterfaces en panne : {down if down else 'aucune'}")

    except NetworkAPIError as e:
        print(f"Erreur reseau : {e}")

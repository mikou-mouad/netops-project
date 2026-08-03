import os
from flask import Flask, jsonify, request

app = Flask(__name__)

SITE_NAME = os.environ.get("SITE_NAME", "site-inconnu")
API_TOKEN = os.environ.get("API_TOKEN", "changeme")
POD_NAME = os.environ.get("HOSTNAME", "inconnu")

INTERFACES = {
    "GigabitEthernet0/1": {"status": "up", "ip": "10.0.1.1", "vlan": 10},
    "GigabitEthernet0/2": {"status": "down", "ip": None, "vlan": 20},
}


def check_token():
    return request.headers.get("X-Api-Token") == API_TOKEN


@app.route("/health")
def health():
    return jsonify({"site": SITE_NAME, "status": "ok", "pod": POD_NAME})


@app.route("/api/devices/<device_id>/interfaces")
def get_interfaces(device_id):
    if not check_token():
        return jsonify({"error": "Token invalide ou manquant"}), 401
    return jsonify({"site": SITE_NAME, "device_id": device_id, "interfaces": INTERFACES})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

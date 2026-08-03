import os
from flask import Flask, jsonify, request

app = Flask(__name__)

SITE_NAME = os.environ.get("SITE_NAME", "site-inconnu")

INTERFACES = {
    "GigabitEthernet0/1": {"status": "up", "ip": "10.0.1.1", "vlan": 10},
    "GigabitEthernet0/2": {"status": "down", "ip": None, "vlan": 20},
    "GigabitEthernet0/3": {"status": "up", "ip": "10.0.3.1", "vlan": 30},
}

@app.route("/api/devices/<device_id>/interfaces", methods=["GET"])
def get_interfaces(device_id):
    return jsonify({"site": SITE_NAME, "device_id": device_id, "interfaces": INTERFACES})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"site": SITE_NAME, "status": "ok"})
               
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
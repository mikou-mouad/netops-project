from flask import Flask, jsonify

app = Flask(__name__)

INTERFACES = {
    "GigabitEthernet0/1": {"status": "up", "ip": "10.0.1.1", "vlan": 10},
    "GigabitEthernet0/2": {"status": "down", "ip": None, "vlan": 20},
    "GigabitEthernet0/3": {"status": "up", "ip": "10.0.3.1", "vlan": 30},
}

@app.route("/api/devices/<device_id>/interfaces", methods=["GET"])
def get_interfaces(device_id):
    return jsonify({"device_id": device_id, "interfaces": INTERFACES})

if __name__ == "__main__":
    app.run(port=5000, debug=True)

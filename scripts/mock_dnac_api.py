import time
import uuid

from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_USER = "admin"
VALID_PASS = "dnacpass123"
VALID_TOKEN = "dnac-fake-token-xyz"

DEVICES = [
    {"id": "dev-siege", "hostname": "siege-router", "managementIpAddress": "10.10.10.1", "reachabilityStatus": "Reachable"},
    {"id": "dev-agence1", "hostname": "agence1-router", "managementIpAddress": "10.10.10.2", "reachabilityStatus": "Reachable"},
    {"id": "dev-agence2", "hostname": "agence2-router", "managementIpAddress": "10.10.10.3", "reachabilityStatus": "Reachable"},
]

FABRIC_ROLES = {
    "dev-siege": ["CONTROL_PLANE_NODE", "BORDER_NODE"],
    "dev-agence1": ["EDGE_NODE"],
    "dev-agence2": ["EDGE_NODE"],
}

TASKS = {}
FABRIC_SITES = {}
ONBOARDED_HOSTS = []

VALID_POOLS = {"VN_CORP": "10.30.0.0/24", "VN_GUEST": "10.30.99.0/24"}


def check_auth_token():
    return request.headers.get("X-Auth-Token") == VALID_TOKEN


def find_device(device_id):
    return next((d for d in DEVICES if d["id"] == device_id), None)


@app.route("/dna/system/api/v1/auth/token", methods=["POST"])
def auth_token():
    auth = request.authorization
    if not auth or auth.username != VALID_USER or auth.password != VALID_PASS:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"Token": VALID_TOKEN})


@app.route("/dna/intent/api/v1/network-device", methods=["GET"])
def network_device():
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401
    return jsonify({"response": DEVICES})


@app.route("/dna/intent/api/v1/template-programmer/template/deploy", methods=["POST"])
def deploy_template():
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401
    body = request.get_json(force=True)
    if not body or "templateId" not in body or "targetInfo" not in body:
        return jsonify({"error": "templateId et targetInfo sont requis"}), 400
    task_id = str(uuid.uuid4())[:8]
    TASKS[task_id] = {"polls": 0}
    return jsonify({"deploymentId": f"dep-{task_id}", "taskId": task_id})


@app.route("/dna/intent/api/v1/task/<task_id>", methods=["GET"])
def get_task(task_id):
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401
    if task_id not in TASKS:
        return jsonify({"response": {"progress": "Unknown task", "isError": True}}), 404
    TASKS[task_id]["polls"] += 1
    if TASKS[task_id]["polls"] < 3:
        return jsonify({"response": {"progress": "IN_PROGRESS", "isError": False, "endTime": None}})
    return jsonify({"response": {"progress": "TEMPLATE_DEPLOYED", "isError": False, "endTime": int(time.time() * 1000)}})


@app.route("/dna/intent/api/v1/business/sda/fabric-site", methods=["POST"])
def create_fabric_site():
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401
    body = request.get_json(force=True)
    site_name = body.get("siteNameHierarchy")
    device_id = body.get("deviceId")
    if not site_name or not device_id:
        return jsonify({"error": "siteNameHierarchy et deviceId sont requis"}), 400
    device = find_device(device_id)
    if not device:
        return jsonify({"error": f"Device inconnu : {device_id}"}), 404

    FABRIC_SITES[site_name] = {
        "siteNameHierarchy": site_name,
        "deviceId": device_id,
        "roles": FABRIC_ROLES.get(device_id, []),
    }
    return jsonify({"status": "success", "site": FABRIC_SITES[site_name]})


@app.route("/dna/intent/api/v1/business/sda/fabric-site", methods=["GET"])
def list_fabric_sites():
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401
    return jsonify({"response": list(FABRIC_SITES.values())})


@app.route("/dna/intent/api/v1/business/sda/hostonboarding/user-device", methods=["POST"])
def onboard_host():
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401
    body = request.get_json(force=True)
    device_id = body.get("deviceId")
    vn_name = body.get("virtualNetworkName")
    interface_name = body.get("interfaceName")

    device = find_device(device_id)
    if not device:
        return jsonify({"error": f"Device inconnu : {device_id}"}), 404
    if vn_name not in VALID_POOLS:
        return jsonify({"error": f"Reseau virtuel inconnu : {vn_name}. Attendu : {list(VALID_POOLS)}"}), 400
    if device["reachabilityStatus"] != "Reachable":
        return jsonify({"error": f"Device {device['hostname']} injoignable, onboarding impossible"}), 409

    entry = {
        "device": device["hostname"],
        "interfaceName": interface_name,
        "virtualNetworkName": vn_name,
        "ipPool": VALID_POOLS[vn_name],
    }
    ONBOARDED_HOSTS.append(entry)
    return jsonify({"status": "success", "onboarding": entry})


@app.route("/dna/intent/api/v1/business/sda/fabric-site/health", methods=["GET"])
def fabric_health():
    if not check_auth_token():
        return jsonify({"error": "Invalid or missing X-Auth-Token"}), 401

    report = []
    for site_name, site in FABRIC_SITES.items():
        device = find_device(site["deviceId"])
        issues = []
        if not device:
            issues.append("Device de la fabric introuvable dans l'inventaire")
        elif device["reachabilityStatus"] != "Reachable":
            issues.append(f"{device['hostname']} ({'/'.join(site['roles'])}) injoignable")

        report.append({
            "site": site_name,
            "status": "HEALTHY" if not issues else "DEGRADED",
            "issues": issues,
        })
    return jsonify({"response": report})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=False)

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

TASKS = {}


def check_auth_token():
    return request.headers.get("X-Auth-Token") == VALID_TOKEN


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=False)

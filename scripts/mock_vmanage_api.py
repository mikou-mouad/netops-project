import secrets
import uuid

from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = "dev-secret-key-not-for-production"

VALID_USER = "admin"
VALID_PASS = "vmanagepass123"

DEVICES = [
    {"deviceId": "vedge-siege", "host-name": "siege-router", "site-id": None, "reachability": "reachable"},
    {"deviceId": "vedge-agence1", "host-name": "agence1-router", "site-id": None, "reachability": "reachable"},
    {"deviceId": "vedge-agence2", "host-name": "agence2-router", "site-id": None, "reachability": "reachable"},
]

XSRF_TOKENS = {}
POLICIES = {}
TASKS = {}


def find_device(device_id):
    return next((d for d in DEVICES if d["deviceId"] == device_id), None)


def configured_site_ids():
    return {d["site-id"] for d in DEVICES if d["site-id"]}


def check_session():
    return session.get("authenticated") is True


def check_xsrf():
    token = request.headers.get("X-XSRF-TOKEN")
    return token and XSRF_TOKENS.get(session.get("sid")) == token


def check_auth():
    return check_session() and check_xsrf()


@app.route("/j_security_check", methods=["POST"])
def j_security_check():
    username = request.form.get("j_username")
    password = request.form.get("j_password")
    if username != VALID_USER or password != VALID_PASS:
        return "Login failed", 401
    session["authenticated"] = True
    session["sid"] = secrets.token_hex(8)
    return "", 200


@app.route("/dataservice/client/token", methods=["GET"])
def client_token():
    if not check_session():
        return jsonify({"error": "Not authenticated"}), 401
    token = secrets.token_hex(16)
    XSRF_TOKENS[session["sid"]] = token
    return token, 200


@app.route("/dataservice/system/device/vedges", methods=["GET"])
def list_vedges():
    if not check_auth():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    return jsonify({"data": DEVICES})


@app.route("/dataservice/system/device/site", methods=["POST"])
def configure_site():
    if not check_auth():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    body = request.get_json(force=True)
    device = find_device(body.get("deviceId"))
    if not device:
        return jsonify({"error": f"Device inconnu : {body.get('deviceId')}"}), 404
    device["site-id"] = body.get("siteId")
    device["tloc-color"] = body.get("tlocColor")
    return jsonify({"status": "success", "device": device})


@app.route("/dataservice/device/omp/summary", methods=["GET"])
def omp_summary():
    if not check_auth():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    device_id = request.args.get("deviceId")
    device = find_device(device_id)
    if not device:
        return jsonify({"error": f"Device inconnu : {device_id}"}), 404
    if not device["site-id"]:
        return jsonify({"data": {"omp-peers-up": 0, "status": "site non configure"}})
    configured_others = [d for d in DEVICES if d["site-id"] and d["deviceId"] != device_id]
    return jsonify({"data": {"omp-peers-up": len(configured_others), "status": "up" if configured_others else "isole"}})


@app.route("/dataservice/template/policy/vsmart", methods=["POST"])
def create_policy():
    if not check_auth():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    body = request.get_json(force=True)
    policy_name = body.get("policyName")
    target_sites = set(body.get("targetSites", []))
    rules = body.get("rules", [])

    if not policy_name or not target_sites or not rules:
        return jsonify({"error": "policyName, targetSites et rules sont requis"}), 400

    missing = target_sites - configured_site_ids()
    if missing:
        return jsonify({"error": f"Site(s) absent(s) de l'overlay SD-WAN, impossible de deployer la policy : {sorted(missing)}"}), 409

    policy_id = f"policy-{uuid.uuid4().hex[:8]}"
    process_id = f"proc-{uuid.uuid4().hex[:8]}"
    POLICIES[policy_id] = {
        "policyName": policy_name,
        "targetSites": sorted(target_sites),
        "rules": rules,
        "active": False,
    }
    TASKS[process_id] = {"policyId": policy_id, "polls": 0}
    return jsonify({"policyId": policy_id, "processId": process_id})


@app.route("/dataservice/device/action/status/<process_id>", methods=["GET"])
def action_status(process_id):
    if not check_auth():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    if process_id not in TASKS:
        return jsonify({"data": {"status": "unknown"}}), 404

    task = TASKS[process_id]
    task["polls"] += 1
    if task["polls"] < 3:
        return jsonify({"data": {"status": "IN_PROGRESS"}})

    POLICIES[task["policyId"]]["active"] = True
    return jsonify({"data": {"status": "Success"}})


@app.route("/dataservice/template/policy/vsmart", methods=["GET"])
def list_policies():
    if not check_auth():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    return jsonify({"data": [{"policyId": pid, **p} for pid, p in POLICIES.items()]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

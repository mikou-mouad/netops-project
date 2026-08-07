import secrets

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


def find_device(device_id):
    return next((d for d in DEVICES if d["deviceId"] == device_id), None)


def check_session():
    return session.get("authenticated") is True


def check_xsrf():
    token = request.headers.get("X-XSRF-TOKEN")
    return token and XSRF_TOKENS.get(session.get("sid")) == token


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
    if not check_session() or not check_xsrf():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    return jsonify({"data": DEVICES})


@app.route("/dataservice/system/device/site", methods=["POST"])
def configure_site():
    if not check_session() or not check_xsrf():
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
    if not check_session() or not check_xsrf():
        return jsonify({"error": "Missing or invalid session/XSRF token"}), 401
    device_id = request.args.get("deviceId")
    device = find_device(device_id)
    if not device:
        return jsonify({"error": f"Device inconnu : {device_id}"}), 404
    if not device["site-id"]:
        return jsonify({"data": {"omp-peers-up": 0, "status": "site non configure"}})

    configured_others = [d for d in DEVICES if d["site-id"] and d["deviceId"] != device_id]
    return jsonify({"data": {"omp-peers-up": len(configured_others), "status": "up" if configured_others else "isole"}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

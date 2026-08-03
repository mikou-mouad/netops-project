from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_USER = "admin"
VALID_PASS = "acipass123"
VALID_TOKEN = "apic-fake-token-xyz"

TENANTS = {}


def check_token():
    return request.headers.get("APIC-Cookie") == VALID_TOKEN


def find_epgs(tenant_body):
    """Parcourt l'arbre poste pour retrouver les EPG et leurs contrats."""
    epgs = {}
    for ap in tenant_body.get("fvTenant", {}).get("children", []):
        if "fvAp" not in ap:
            continue
        for epg_wrapper in ap["fvAp"].get("children", []):
            if "fvAEPg" not in epg_wrapper:
                continue
            epg = epg_wrapper["fvAEPg"]
            name = epg["attributes"]["name"]
            contracts = {"consumes": [], "provides": []}
            for rel in epg.get("children", []):
                if "fvRsCons" in rel:
                    contracts["consumes"].append(rel["fvRsCons"]["attributes"]["tnVzBrCPName"])
                if "fvRsProv" in rel:
                    contracts["provides"].append(rel["fvRsProv"]["attributes"]["tnVzBrCPName"])
            epgs[name] = contracts
    return epgs


@app.route("/api/aaaLogin.json", methods=["POST"])
def aaa_login():
    body = request.get_json(force=True)
    creds = body.get("aaaUser", {}).get("attributes", {})
    if creds.get("name") != VALID_USER or creds.get("pwd") != VALID_PASS:
        return jsonify({"imdata": [{"error": {"attributes": {"text": "Unauthorized"}}}]}), 401
    return jsonify({"imdata": [{"aaaLogin": {"attributes": {"token": VALID_TOKEN}}}]})


@app.route("/api/mo/uni/tn-<tenant_name>.json", methods=["POST"])
def deploy_tenant(tenant_name):
    if not check_token():
        return jsonify({"imdata": [{"error": {"attributes": {"text": "Missing or invalid APIC-Cookie"}}}]}), 401
    body = request.get_json(force=True)
    if "fvTenant" not in body:
        return jsonify({"imdata": [{"error": {"attributes": {"text": "fvTenant racine requis"}}}]}), 400

    TENANTS[tenant_name] = body
    return jsonify({"imdata": [{"fvTenant": {"attributes": {"name": tenant_name, "status": "created,modified"}}}]})


@app.route("/api/mo/uni/tn-<tenant_name>.json", methods=["GET"])
def get_tenant(tenant_name):
    if not check_token():
        return jsonify({"imdata": [{"error": {"attributes": {"text": "Missing or invalid APIC-Cookie"}}}]}), 401
    if tenant_name not in TENANTS:
        return jsonify({"imdata": []}), 404
    return jsonify({"imdata": [TENANTS[tenant_name]]})


@app.route("/api/mo/uni/tn-<tenant_name>/contract-check.json", methods=["GET"])
def contract_check(tenant_name):
    """Endpoint de validation (non standard APIC, ajoute pour ce TP) :
    verifie qu'un contrat relie bien deux EPG donnes en parametres."""
    if not check_token():
        return jsonify({"imdata": [{"error": {"attributes": {"text": "Missing or invalid APIC-Cookie"}}}]}), 401
    if tenant_name not in TENANTS:
        return jsonify({"error": f"Tenant {tenant_name} introuvable"}), 404

    consumer = request.args.get("consumer")
    provider = request.args.get("provider")
    epgs = find_epgs(TENANTS[tenant_name])

    if consumer not in epgs or provider not in epgs:
        return jsonify({"allowed": False, "reason": "EPG consumer ou provider introuvable"}), 404

    consumer_contracts = set(epgs[consumer]["consumes"])
    provider_contracts = set(epgs[provider]["provides"])
    shared = consumer_contracts & provider_contracts

    if shared:
        return jsonify({"allowed": True, "contract": list(shared)[0]})
    return jsonify({"allowed": False, "reason": "Aucun contrat commun entre ces EPG (trafic refuse par defaut dans ACI)"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000, debug=False)

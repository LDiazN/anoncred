from typing import Any, Dict
from httpx import Client
import ooniauth_py as ooni
from anoncred.utils import to_str, to_bin


def test_manifest(client):
    r = client.get("/manifest")
    assert r.status_code == 200, r.json()


def test_workflow(client):
    # Assume server is initialized 

    # Registration
    resp = getj(client, "/manifest")
    pp_s : str = resp['public_parameters']
    pp = to_bin(pp_s)
    user = ooni.UserState(pp)
    reg_request = user.make_register_request()
    reg_response = postj(client, "/register", json= {
        "credential_sign_request" : to_str(reg_request),
        "manifest_version" : resp['version']
    })

    response_bin = to_bin(reg_response['credential_sign_response'])
    emission_date = reg_response['emission_date'] # Credentials are valid for 30 days

    user.handle_registration_response(response_bin)

    # Submission
    submit_req = user.make_submit_request(probe_asn="AS1234", probe_cc="VE", emission_date=emission_date)

    submit_resp = postj(client, "/submit", json={
        "nym" : to_str(submit_req.nym),
        "submit_request" : to_str(submit_req.request),
        "measurement" : {
            "probe_cc" : "VE",
            "probe_asn" : "AS1234",
            "test_name" : "web_connectivity"
        },
        "age_range" : [emission_date - 30, emission_date + 1],
        "measurement_count_range" : [0, 100]
    })

    submit_bin = to_bin(submit_resp['submit_response'])
    user.handle_submit_response(submit_bin)

def getj(client: Client, path : str):
    resp = client.get(path)
    assert resp.status_code == 200, f"Unexpected status code: {resp.status_code}: {resp.content}"
    return resp.json()

def postj(client: Client, path : str, json : Dict[str, Any]):
    resp = client.post(path, json=json)
    assert resp.status_code == 200, f"Unexpected status code: {resp.status_code}: {resp.content}"
    return resp.json()
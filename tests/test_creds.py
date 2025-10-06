import ooniauth_py as ooni
from .utils import getj, postj, submit_request
import logging
log = logging.getLogger(__file__)


def test_manifest(client):
    r = client.get("/manifest")
    assert r.status_code == 200, r.json()

def test_library():
    # test only the library, without going through the API
    server = ooni.ServerState()
    pp = server.get_public_parameters()
    client = ooni.UserState(pp)

    # Test registration
    reg_request = client.make_registration_request()
    resp = server.handle_registration_request(reg_request)
    client.handle_registration_response(resp)

def test_basic_usage(client):
    # Assume server is initialized

    # Registration
    resp = getj(client, "/manifest")
    pp: str = resp["public_parameters"]
    user = ooni.UserState(pp)
    reg_request = user.make_registration_request()
    
    reg_response = postj(
        client,
        "/register",
        json={
            "credential_sign_request": reg_request,
            "manifest_version": resp["version"],
        },
    )

    response = reg_response["credential_sign_response"]
    emission_date = reg_response["emission_date"]  # Credentials are valid for 30 days

    user.handle_registration_response(response)


    # Submission
    response = submit_request(user, client, "AS1234", "VE", emission_date)
    user.handle_submit_response(response)

    # try more submissions
    response = submit_request(user, client, "AS4321", "ES", emission_date)
    user.handle_submit_response(response)

    response = submit_request(user, client, "AS9999", "IT", emission_date)
    user.handle_submit_response(response)

    # Check that measurements where saved to DB
    resp = getj(client, "/measurements")
    assert len(resp["results"]) == 3


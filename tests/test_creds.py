import ooniauth_py as ooni
from anoncred.utils import to_str, to_bin
from .utils import getj, postj, submit_request


def test_manifest(client):
    r = client.get("/manifest")
    assert r.status_code == 200, r.json()


def test_basic_usage(client):
    # Assume server is initialized

    # Registration
    resp = getj(client, "/manifest")
    pp_s: str = resp["public_parameters"]
    pp = to_bin(pp_s)
    user = ooni.UserState(pp)
    reg_request = user.make_registration_request()
    reg_response = postj(
        client,
        "/register",
        json={
            "credential_sign_request": to_str(reg_request),
            "manifest_version": resp["version"],
        },
    )

    response_bin = to_bin(reg_response["credential_sign_response"])
    emission_date = reg_response["emission_date"]  # Credentials are valid for 30 days

    user.handle_registration_response(response_bin)

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


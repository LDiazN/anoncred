from .utils import getj, postj
import ooniauth_py as ooni
from anoncred.utils import to_bin, to_str

def test_bench_registration(benchmark, client):
    """
    This test will benchmark register and submission API endpoints.
    Note that we avoid including user time, we only care about server timings
    """
    # Assume server is initialized

    # Registration
    resp = getj(client, "/manifest")
    pp_s: str = resp["public_parameters"]
    pp = to_bin(pp_s)
    user = ooni.UserState(pp)
    reg_request = to_str(user.make_registration_request())

    def register():
        postj(
            client,
            "/register",
            json={
                "credential_sign_request": reg_request,
                "manifest_version": resp["version"],
            },
        )
    
    benchmark(register)



def test_bench_submit(benchmark, client):

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
    asn = "AS1234"
    cc = "VE"

    submit_req = user.make_submit_request(
        probe_asn=asn, probe_cc=cc, emission_date=emission_date
    )
    nym = to_str(submit_req.nym)
    req = to_str(submit_req.request)

    def submit():
        resp = client.post(
            "/submit",
            json={
                "nym": nym,
                "submit_request": req,
                "measurement": {
                    "probe_cc": cc,
                    "probe_asn": asn,
                    "test_name": "web_connectivity",
                },
                "age_range": [emission_date - 30, emission_date + 1],
                "measurement_count_range": [0, 100],
            },
        )
        assert resp.status_code == 200
    
    benchmark(submit)

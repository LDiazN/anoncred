import ooniauth_py as ooni
from typing import Any, Dict
from httpx import Client

def submit_request(
    user: ooni.UserState,
    client: Client,
    probe_asn: str,
    probe_cc: str,
    emission_date: int,
    submit_req: ooni.SubmitRequest | None = None
) -> str:

    if submit_req is None:
        submit_req = user.make_submit_request(
            probe_asn=probe_asn, probe_cc=probe_cc, emission_date=emission_date
        )

    submit_resp = postj(
        client,
        "/submit",
        json={
            "nym": submit_req.nym,
            "submit_request": submit_req.request,
            "measurement": {
                "probe_cc": probe_cc,
                "probe_asn": probe_asn,
                "test_name": "web_connectivity",
            },
            "age_range": [emission_date - 30, emission_date + 1],
            "measurement_count_range": [0, 100],
        },
    )

    return submit_resp["submit_response"]


def getj(client: Client, path: str):
    resp = client.get(path)
    assert resp.status_code == 200, (
        f"Unexpected status code: {resp.status_code}: {resp.content}"
    )
    return resp.json()


def postj(client: Client, path: str, json: Dict[str, Any]):
    resp = client.post(path, json=json)
    assert resp.status_code == 200, (
        f"Unexpected status code: {resp.status_code}: {resp.content}"
    )
    return resp.json()
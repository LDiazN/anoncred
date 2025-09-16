from httpx import Client
from typing import Dict, Any
from pydantic import BaseModel
from anoncred.protocol import (
    Issuance,
    PRF,
    get_nym_id,
    compute_cred_sign_request,
    get_age,
    get_msmnt_cnt,
    Submission,
)
import random
from anoncred.utils import to_str, to_bin
import json

RNG = lambda: random.randint(0, 9999)


class UserAuthCredentials(BaseModel):
    """
    user stores this information persistently
    """


class Probe:
    """
    Emulates the behaviour of a probe login in with anonymous
    credentials.
    The internal class state represents persisted information
    """

    def __init__(self, client: Client) -> None:
        self.client: Client = client

        # These variables represents the persistent storage of a probe
        self.public_params: bytes | None = None
        self.manifest_version: str
        self.credential_signature: str
        self.public_sign_key: str
        self.credential: bytes
        self.state: Dict[str, Any] = {}
        self.nym_scope: str
        self.age: int
        self.msmnt_count: int

    def get_manifest(self):
        r = self.client.get("manifest")
        assert r.status_code == 200
        j = r.json()
        self.public_params = j["public_parameters"]
        self.manifest_version = j["version"]
        self.nym_scope = j["nym_scope"]

    def register(self):
        assert self.public_params, (
            "I can only register if I have the server's public params"
        )
        credential_sign_request_bin = Issuance.prepare(RNG, self.public_params)

        credential_sign_request = to_str(credential_sign_request_bin)

        r = self.client.post(
            "register",
            json={
                "manifest_version": self.manifest_version,
                "credential_sign_request": credential_sign_request,
            },
        )
        assert r.status_code == 200
        j = r.json()

        self.credential_signature = j["signature"]
        self.public_sign_key = j["public_sign_key"]
        self.age = get_age(j["credential_sign_response"])
        self.msmnt_count = get_msmnt_cnt(j["credential_sign_response"])

        # Validate credentials
        credential = to_bin(j["credential_sign_response"])
        self.credential = Issuance.finalize(self.state, credential)

    def submit_measurement(self):
        nym_scope = self.nym_scope.replace("{probe_cc}", self.get_cc()).replace(
            "{probe_asn}", self.get_asn()
        )
        nym = PRF(nym_id=get_nym_id(self.credential), nym_scope=nym_scope)

        # TODO Q? What do we do with this credential sign request? I guess it's sent with the
        # request but it's not mentioned in the spec
        new_cred_sign_request = compute_cred_sign_request(
            self.age, self.msmnt_count, get_nym_id(self.credential)
        )
        # Used to compute presentation_message binary buffer
        parameters = {
            "nym": to_str(nym),
            "age_lsb": self.get_age_lsb(),
            "msmnt_count_lsb": self.get_msmnt_count_lsb(),
        }

        parameters_bin = json.dumps(parameters).encode()
        presentation_message, state = Submission.prepare(RNG, parameters_bin)
        submit_req = dict(
            credential_sign_request=to_str(new_cred_sign_request),
            measurement={
                # TODO: Q? Not sure what's the blocklist, we need more details on how to construct it
                "blocklist": [],
                "data": f"Data for measurement {self.msmnt_count}",
            },
            presentation_message=to_str(presentation_message),
        )

        r = self.client.post("submit", json=submit_req)

        assert r.status_code == 200, r.json()

    def get_age_lsb(self) -> int:
        # Magically get only the least significant bytes
        return self.age

    def get_msmnt_count_lsb(self) -> int:
        # Magically get only the least significant bytes
        return self.msmnt_count

    def get_cc(self):
        return "VE"

    def get_asn(self):
        return "AS1234"

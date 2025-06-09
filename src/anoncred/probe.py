from httpx import Client
from typing import Dict, Any
from pydantic import BaseModel
from anoncred.protocol import Issuance
import random
from anoncred.utils import to_str, to_bin


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
        # We only store what the client stores permanently.
        self.public_params: bytes | None = None
        self.manifest_version: str
        self.credential_signature: str
        self.public_sign_key: str
        self.credential: bytes
        self.state: Dict[str, Any] = {}

    def get_manifest(self):
        r = self.client.get("manifest")
        assert r.status_code == 200
        j = r.json()
        self.public_params = j["public_parameters"]
        self.manifest_version = j["version"]

    def register(self):
        assert (
            self.public_params
        ), "I can only register if I have the server's public params"
        credential_sign_request_bin = Issuance.prepare(
            lambda: random.randint(0, 9999), self.public_params
        )

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

        self.credential_signature = j['signature']
        self.public_sign_key = j['public_sign_key']

        # Validate credentials
        credential = to_bin(j['credential_sign_request'])
        self.credential = Issuance.finalize(self.state, credential)



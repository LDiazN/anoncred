import random
from typing import Callable, Any, Tuple


def rng() -> int:
    return random.randint(0, 999999)


CredentialSignRequest = bytes
CredentialSignResponse = bytes
PresentationMessage = bytes
PresentationReply = bytes
Credential = bytes
#! Note that the actual RNG should be cryptographically secure
Rng = Callable[[], int]

# TODO Rustify
def get_nym_from_presentation_message(presetation: PresentationMessage) -> bytes:
    return b"nym"

# TODO Rustify
def get_nym_id(data: bytes) -> bytes:
    return b"nym_id"


# TODO Rustify
def get_age(sign_request: CredentialSignRequest | CredentialSignResponse) -> int:
    return 42


# TODO Rustify
def get_msmnt_cnt(sign_request: CredentialSignRequest | CredentialSignResponse) -> int:
    return 69


# TODO Rustify
def compute_cred_sign_request(age: int, msmnt_count: int, nym_id: bytes) -> bytes:
    return (
        age.to_bytes(4, byteorder="little")
        + b";"
        + msmnt_count.to_bytes(4, byteorder="little")
        + b";"
        + nym_id
    )


# TODO Rustify
# nym_scope here should be replaced with the actual values of probe_cc and probe_asn
def PRF(nym_id: bytes, nym_scope: str) -> bytes:
    return nym_id + nym_scope.encode()


class Issuance:

    # TODO Rustify
    @staticmethod
    def prepare(rng: Rng, public_parameters: bytes) -> CredentialSignRequest:
        return b"deadbeef"

    # TODO Rustify
    @staticmethod
    def handle(rng: Rng, sign_request: CredentialSignRequest) -> CredentialSignResponse:
        # Assumes everything goes fine
        return b"everything ok"

    # TODO Rustify
    # TODO What does this do? is it mutating the state?
    @staticmethod
    def finalize(state: Any, response: CredentialSignResponse) -> Credential:
        return b"credential"

class Submission:

    # TODO Rustify
    @staticmethod
    def prepare(rng: Rng, parameters : bytes) -> Tuple[bytes, Any]:
        """
        # Returns 
        (credential_submission_preparation, state)
        """
        return (b'preparation successful', {})

    # TODO Rustify
    @staticmethod
    def handle(rng: Rng, sign_request: PresentationMessage) -> PresentationReply:
        # Assumes everything goes fine
        return b"everything ok"
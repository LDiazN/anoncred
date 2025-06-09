import random
from typing import Callable, Any
import json

def rng() -> int:
    return random.randint(0, 999999)

CredentialSignRequest = bytes
CredentialSignResponse = bytes
Credential = bytes
Rng = Callable[[], int]

# TODO Rustify
def get_nym(sign_request : CredentialSignRequest | CredentialSignResponse) -> bytes:
    return b'1234'

def get_age(sign_request : CredentialSignRequest | CredentialSignResponse) -> int:
    return 42

def get_msmnt_cnt(sign_request : CredentialSignRequest | CredentialSignResponse) -> int:
    return 69

class Issuance:

    # TODO Rustify
    @staticmethod
    def prepare(rng : Rng, public_parameters : bytes) -> CredentialSignRequest:
        return b'deadbeef'
    
    # TODO Rustify
    @staticmethod
    def handle(rng : Rng, sign_request : CredentialSignRequest) -> CredentialSignResponse:
        # Assumes everything goes fine
        return b'everything ok'
    
    # TODO What does this do? is it mutating the state?
    @staticmethod
    def finalize(state : Any, response : CredentialSignResponse) -> Credential:
        return b'credential'

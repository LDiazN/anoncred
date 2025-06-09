from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from anoncred.utils import to_bin, to_str
from anoncred.models import UserAuthCredential, create_db_and_tables, SigningKeyPair
from anoncred.protocol import (
    get_nym,
    Issuance,
)
from pydantic import BaseModel
from .dependencies import SessionDep
import random

app = FastAPI()


@app.get("/")
def read_root():
    return {"Welcome": "Too ooni anonymous credentials protocol"}


class Measurement(BaseModel):
    data: str


# -- < Manifest > ------------------------------------
@app.get("/manifest")
def manifest():
    # This is the `access_policy_manifest`
    return {
        # nym_scope Is a format string, to be filled later by the user and the server during the presentation of a credential.
        "nym_scope": "ooni.org/{probe_cc}/{probe_asn}",
        "public_parameters": "0xdeadbeef",
        "submission_policy": {
            "NL/AS9080": {"age": [5, 10], "measurement_count": 100},
            "US": {"measurement_count": 10},
        },
        "version": "0.1-b13a37b4b3",
    }


# -- < Registration > --------------------------------
class RegisterRequest(BaseModel):
    manifest_version: str
    # Crypto component
    credential_sign_request: str


class RegisterResponse(BaseModel):
    signature: str
    public_sign_key: str
    # Crypto component
    credential_sign_response: str


@app.post("/register", response_model=RegisterResponse)
def register(request: RegisterRequest, session: SessionDep, response: Response):

    # Decode binary array
    cred_sign_req_str = request.credential_sign_request
    cred_sign_req = to_bin(cred_sign_req_str)

    # Handle request
    cred_sign_response = Issuance.handle(lambda: random.randint(0, 9999), cred_sign_req)

    # Create new credential and store it in the server
    nym_id = get_nym(cred_sign_response)
    user_cred = UserAuthCredential(nym_id=nym_id)
    session.add(user_cred)
    session.commit()
    session.refresh(user_cred)

    # Sign
    key = SigningKeyPair.get_latest_key(session)
    signature = key.sign(cred_sign_response)
    signature_str = to_str(signature)

    # TODO Q?: Shouldn't we provide a public signing key as well in the body? The user should send it
    # to get the original secret signing key
    return RegisterResponse(
        credential_sign_response=to_str(cred_sign_response),
        signature=signature_str,
        public_sign_key=key.public_key,
    )


# -- < Submission > ----------------------------------
@app.post("/submit")
def submit():
    return {"submir": "hello"}


# -- < Credential update > ---------------------------


@app.post("/update/credentials")
def update_credentials():
    return {"update_credentials"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

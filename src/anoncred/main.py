from contextlib import asynccontextmanager
from sqlmodel import select
from fastapi import FastAPI
from .utils import to_http_excepion
from .models import create_db_and_tables, init_server_state
from . import models
from pydantic import BaseModel
from .dependencies import SessionDep, ServerStateDep
from ooniauth_py import DeserializationFailed, ProtocolError, CredentialError
import logging

log = logging.getLogger(__file__)


# -- < Life Cycle >  --------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    init_server_state()
    yield


app = FastAPI(lifespan=lifespan)


# -- < API > ----------------------------------------
@app.get("/")
def read_root():
    return {"Welcome": "Too ooni anonymous credentials protocol"}


class Measurement(BaseModel):
    test_name: str
    probe_cc: str
    probe_asn: str
    # ... more data


# -- < Manifest > ------------------------------------
@app.get("/manifest")
def manifest(server_state: ServerStateDep):
    public_params = server_state.get_public_parameters()

    return {
        # nym_scope Is a format string, to be filled later by the user and the server during the presentation of a credential.
        "nym_scope": "ooni.org/{probe_cc}/{probe_asn}",
        "public_parameters": public_params,
        "submission_policy": {
            "NL/AS9080": {"age": [5, 10], "measurement_count": 100},
            "US": {"measurement_count": 10},
        },
        "version": "0.1-b13a37b4b3",
    }


# -- < Registration > --------------------------------
class RegisterRequest(BaseModel):
    manifest_version: str
    credential_sign_request: str


class RegisterResponse(BaseModel):
    credential_sign_response: str
    emission_date: int


@app.post("/register", response_model=RegisterResponse)
def register(request: RegisterRequest, session: SessionDep, state: ServerStateDep):
    req = request.credential_sign_request
    try:
        result = state.handle_registration_request(req)
    except (ProtocolError, CredentialError, DeserializationFailed) as e:
        raise to_http_excepion(e)

    return RegisterResponse(
        credential_sign_response=result, emission_date=state.today()
    )


# -- < Submission > ----------------------------------
class SubmitRequest(BaseModel):
    measurement: Measurement # convert this to string

    # New
    submit_request: str
    nym: str
    age_range: list[int]  # [10, 30]
    measurement_count_range: list[int]  # [100, 200]
    is_verified: bool  | None = None # filled by the server before saved to disk


class SubmitResponse(BaseModel):
    submit_response: str


@app.post("/submit", response_model=SubmitResponse)
def submit(request: SubmitRequest, session: SessionDep, state: ServerStateDep):

    try:
        result = state.handle_submit_request(
            request.nym,
            request.submit_request,
            request.measurement.probe_cc,
            request.measurement.probe_asn,
            request.age_range,
            request.measurement_count_range,
        )
    except (ProtocolError, CredentialError) as e:
        raise to_http_excepion(e)

    session.add(
        models.Measurement(
            nym=request.nym,
            probe_cc=request.measurement.probe_cc,
            probe_asn=request.measurement.probe_asn,
            test_name=request.measurement.test_name,
        )
    )
    session.commit()

    return SubmitResponse(submit_response=result)


class MeasurementsResponse(BaseModel):
    results: list[Measurement]


# This is mostly a debug endpoint just to see when the data is stored on db
@app.get("/measurements", response_model=MeasurementsResponse)
def get_measurements(session: SessionDep):
    q = select(models.Measurement).limit(100)
    results = session.scalars(q)
    response = MeasurementsResponse(results=[])
    for result in results:
        response.results.append(
            Measurement(
                test_name=result.test_name,
                probe_cc=result.probe_cc,
                probe_asn=result.probe_asn,
            )
        )

    return response

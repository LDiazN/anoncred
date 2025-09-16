from contextlib import asynccontextmanager
from fastapi import HTTPException
from sqlmodel import select
from fastapi import FastAPI, Response
from .utils import to_bin, to_str
from .models import create_db_and_tables, init_server_state
from . import models
from pydantic import BaseModel
from .dependencies import SessionDep, ServerStateDep
import base64
import logging

logger = logging.getLogger(__file__)


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
    # This is the `access_policy_manifest`
    public_params = server_state.get_public_parameters()
    public_params_s = base64.b64encode(public_params).decode()

    return {
        # nym_scope Is a format string, to be filled later by the user and the server during the presentation of a credential.
        "nym_scope": "ooni.org/{probe_cc}/{probe_asn}",
        "public_parameters": public_params_s,
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
    req_s = request.credential_sign_request
    req = to_bin(req_s)
    result = state.handle_registration_request(req)
    return RegisterResponse(
        credential_sign_response=to_str(result), emission_date=state.today()
    )


# -- < Submission > ----------------------------------
class SubmitRequest(BaseModel):
    measurement: Measurement
    submit_request: str
    nym: str
    age_range: list[int]  # [10, 30]
    measurement_count_range: list[int]  # [100, 200]


class SubmitResponse(BaseModel):
    submit_response: str


@app.post("/submit", response_model=SubmitResponse)
def submit(request: SubmitRequest, session: SessionDep, state: ServerStateDep):
    request_bin = to_bin(request.submit_request)
    nym_bin = to_bin(request.nym)

    result = state.handle_submit_request(
        nym_bin,
        request_bin,
        request.measurement.probe_cc,
        request.measurement.probe_asn,
        request.age_range,
        request.measurement_count_range,
    )

    session.add(
        models.Measurement(
            nym=nym_bin,
            probe_cc=request.measurement.probe_cc,
            probe_asn=request.measurement.probe_asn,
            test_name=request.measurement.test_name,
        )
    )
    session.commit()

    return SubmitResponse(submit_response=to_str(result))


class MeasurementsResponse(BaseModel):
    results: list[Measurement]


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


# -- < Credential update > ---------------------------
@app.post("/update/credentials")
def update_credentials():
    return {"update_credentials"}

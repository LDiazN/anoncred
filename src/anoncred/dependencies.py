from typing import Annotated
from fastapi import Depends
from .models import ServerState
from anoncred.models import engine
from sqlmodel import Session
import ooniauth_py
import logging

log = logging.getLogger(__file__)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_server_state(session: SessionDep) -> ooniauth_py.ServerState:
    # will crash if not present
    q = ServerState.get_latest(session)
    return ooniauth_py.ServerState.from_creds(
        q.public_parameters, secret_key=q.secret_key
    )


ServerStateDep = Annotated[ooniauth_py.ServerState, Depends(get_server_state)]

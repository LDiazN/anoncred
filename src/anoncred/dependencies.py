from typing import Annotated
from fastapi import Depends
from .models import ServerState
from anoncred.models import engine
from sqlmodel import Session
import ooniauth_py
from sqlalchemy import select


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_server_state(session: SessionDep) -> ooniauth_py.ServerState:
    q = select(ServerState).limit(1)
    obj = session.scalar(q)

    if obj is not None:
        return ooniauth_py.ServerState.from_creds(
            obj.public_parameters, secret_key=obj.secret_key
        )
    else:
        raise ValueError("Server State not initialized")


ServerStateDep = Annotated[ooniauth_py.ServerState, Depends(get_server_state)]

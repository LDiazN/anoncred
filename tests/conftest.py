from typing import Callable
from pathlib import Path
from anoncred.models import Session
from anoncred.main import app
from anoncred.dependencies import get_session
from anoncred.models import ServerState
import ooniauth_py as ooni
from fastapi.testclient import TestClient
import pytest
from sqlmodel import SQLModel, create_engine
import random
import string
import os


def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    return "".join(random.choices(characters, k=length))


@pytest.fixture
def fake_get_session():
    sqlite_file_name = f"{generate_random_string()}.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)

    SQLModel.metadata.create_all(engine)

    def get_session():
        with Session(engine) as session:
            add_server_state(session)
            yield session

    yield get_session

    db_path = Path(sqlite_file_name)
    if db_path.exists():
        os.remove(sqlite_file_name)


@pytest.fixture
def session(fake_get_session):
    yield fake_get_session()


@pytest.fixture
def client(fake_get_session: Callable[[], Session]):
    app.dependency_overrides[get_session] = fake_get_session
    client = TestClient(app)
    yield client


def add_server_state(session: Session):
    state = ooni.ServerState()
    db_state = ServerState(
        secret_key=state.get_secret_key(),
        public_parameters=state.get_public_parameters(),
    )
    session.add(db_state)
    session.commit()
    session.refresh(db_state)

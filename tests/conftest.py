from typing import Callable
from pathlib import Path
from anoncred.models import engine, Session, SigningKeyPair
from anoncred.main import app
from anoncred.dependencies import SessionDep, get_session
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
            add_signing_keys(session)
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


def add_signing_keys(session: Session):
    keys = SigningKeyPair(public_key="public", secret_key="secret")
    session.add(keys)
    session.commit()
    session.refresh(keys)

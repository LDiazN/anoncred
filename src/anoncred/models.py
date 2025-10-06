from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import Column
from sqlmodel import col
from typing_extensions import Self
from datetime import datetime, timezone
import ooniauth_py as ooniauth
import logging

log = logging.getLogger(__file__)


class ServerState(SQLModel, table=True):
    """
    TODO Think about a proper way to store this data
    """

    id: int = Field(primary_key=True, nullable=True, default=None)
    secret_key: str = Field()
    public_parameters: str = Field()
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_latest(cls, session: Session) -> Self:
        q = select(cls).order_by(col(cls.creation_date).desc()).limit(1)
        return session.exec(q).one()

    @classmethod
    def update(cls, state: ooniauth.ServerState, session: Session):
        entry = cls.get_latest(session)
        entry.public_parameters = state.get_public_parameters()
        entry.secret_key = state.get_secret_key()
        session.add(entry)
        session.commit()


class Measurement(SQLModel, table=True):
    id: int = Field(primary_key=True, default=None)
    nym: str = Field()
    probe_cc: str = Field()
    probe_asn: str = Field()
    test_name: str = Field()
    # ... more data


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def init_server_state():
    with Session(engine) as session:
        try:
            ServerState.get_latest(session)
        except Exception:
            # not existent, create a new one
            log.error("Initial state not found, creating...")
            state = ooniauth.ServerState()
            db_state = ServerState(
                secret_key=state.get_secret_key(),
                public_parameters=state.get_public_parameters(),
            )
            session.add(db_state)
            session.commit()

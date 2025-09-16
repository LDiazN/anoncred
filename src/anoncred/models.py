from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import Column, JSON, BINARY, insert
from sqlmodel import col
from typing_extensions import Self
from datetime import datetime, timezone
import hmac
import hashlib
import ooniauth_py as ooniauth
import logging

logger = logging.getLogger(__file__)


class UserAuthCredential(SQLModel, table=True):
    """
    Similar to an user profile
    """

    id: int | None = Field(primary_key=True, default=None)
    # base64 encoded binary string
    nym_id: bytes = Field(sa_column=Column(BINARY(20), index=True))
    age: int = Field(default=0)
    measurement_count: int = Field(
        default=0,
        nullable=False,
    )

class ServerState(SQLModel, table=True):
    """
    TODO Think about a proper way to store this data 
    """
    id: int = Field(primary_key=True, nullable=True, default=None)
    secret_key: bytes = Field()
    public_parameters: bytes = Field()

    @classmethod
    def update(cls, state : ooniauth.ServerState, session : Session):
        q = select(cls).limit(1)
        entry = session.scalar(q)
        assert entry is not None, "Missing server state entry"
        entry.public_parameters = state.get_public_parameters()
        entry.secret_key = state.get_secret_key()
        session.commit()
        
class BlockListEntry(SQLModel, table = True):
    """
    A table with blocked nyms
    """
    nym: bytes = Field(primary_key=True)


class SigningKeyPair(SQLModel, table=True):
    id: int = Field(primary_key=True, nullable=True, default=None)
    public_key: str = Field(index=True)
    secret_key: str = Field()
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_latest_key(cls, session: Session) -> Self:
        q = select(cls).order_by(col(cls.creation_date).desc()).limit(1)
        return session.exec(q).one()

    def sign(self, data: bytes) -> bytes:
        key_bytes = self.secret_key.encode("utf-8")
        return hmac.new(key_bytes, data, hashlib.sha256).digest()


class Measurement(SQLModel, table=True):
    id: int = Field(primary_key=True, default=None)
    nym: bytes = Field(sa_column=Column(BINARY(32)))
    probe_cc: str = Field()
    probe_asn: str = Field()
    test_name: str  = Field()
    # ... more data


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def init_server_state():
    with Session(engine) as session:
        q = select(ServerState).limit(1)
        results = session.scalars(q)
        if len(results.all()) == 0:
            logger.error("Initial state not found, creating...")
            state = ooniauth.ServerState()
            db_state = ServerState(secret_key=state.get_secret_key(), public_parameters=state.get_public_parameters())
            session.add(db_state)
            session.commit()
        else: 
            logger.error("DB State already initialized")

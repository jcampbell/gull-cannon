import logging
import os
import secrets
import string

from sqlalchemy.engine import create_engine
from sqlalchemy import Column, CHAR, BOOLEAN, ForeignKey, BIGINT
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, TEXT
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy_cockroachdb import run_transaction

logger = logging.getLogger(__name__)
Base = declarative_base()

_engine = None
_Session = None


def get_engine():
    global _engine
    if _engine is None:
        connection_string = os.environ.get("CONNECTION_STRING")
        if not connection_string:
            logger.error("No connection string available; please set CONNECTION_STRING environment variable.")
            exit()

        _engine = create_engine(connection_string)
    return _engine


def get_sessionmaker():
    global _Session
    if _Session is None:
        engine = get_engine()
        _Session = sessionmaker(engine)
    return _Session


def generate_token():
    vocab = string.ascii_letters + string.digits
    return ''.join(secrets.choice(vocab) for _ in range(40))


class Checkin(Base):
    __tablename__ = 'checkins'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())
    headers = Column(JSONB)
    payload = Column(JSONB)


class CallbackDelay(Base):
    __tablename__ = 'callback_delays'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_by = Column(TEXT, ForeignKey('users.username'))
    interval = Column(BIGINT, default=5 * 60 * 1000)


class User(Base):
    __tablename__ = 'users'
    username = Column(TEXT, primary_key=True)
    token = Column(CHAR(40), index=True, default=generate_token)


class Action(Base):
    __tablename__ = 'actions'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4(), index=True)
    username = Column(TEXT, ForeignKey("users.username"))
    user = relationship(User)
    datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())
    action = Column(TEXT, nullable=False)
    duration = Column(BIGINT, default=1000)
    completed = Column(BOOLEAN, default=False)


def init_db(test_token=None):
    engine = get_engine()
    Session = get_sessionmaker()

    Base.metadata.create_all(engine)
    if test_token is not None:
        initial_user = User(
            username="james.p.campbell@gmail.com",
            token=test_token
        )
    else:
        initial_user = User(
            username="james.p.campbell@gmail.com",
        )

    def add_or_update_user(s):
        user = s.query(User).where(User.username == initial_user.username).one_or_none()
        if user and test_token:
            user.token = test_token
        elif not user:
            s.add(initial_user)
        else:
            pass

    run_transaction(Session, lambda s: add_or_update_user(s))

    initial_interval = CallbackDelay(updated_by=initial_user.username)
    run_transaction(Session, lambda s: s.add(initial_interval))


if __name__ == "__main__":
    init_db()


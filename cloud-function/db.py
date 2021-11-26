import logging
import os

from sqlalchemy.engine import create_engine
from sqlalchemy import Column, CHAR, BOOLEAN, ForeignKey, BIGINT
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, TEXT
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)
Base = declarative_base()
connection_string = os.environ.get("CONNECTION_STRING")
if not connection_string:
    logger.error("No connection string available; please set CONNECTION_STRING environment variable.")
    exit()

engine = create_engine(connection_string)
Session = sessionmaker(engine)


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
    token = Column(CHAR(40), index=True)


class Action(Base):
    __tablename__ = 'actions'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4(), index=True)
    username = Column(TEXT, ForeignKey("users.username"))
    user = relationship(User)
    datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())
    action = Column(TEXT, nullable=False)
    duration = Column(BIGINT, default=1000)
    completed = Column(BOOLEAN, default=False)


if __name__ == "__main__":
    Base.metadata.create_all(engine)


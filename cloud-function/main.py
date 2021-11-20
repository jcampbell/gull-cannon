import os
import logging

import flask
from sqlalchemy.engine import create_engine

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy_cockroachdb import run_transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
connection_string = os.environ.get("CONNECTION_STRING")
if not connection_string:
    logger.error("No connection string available; please set CONNECTION_STRING environment variable.")
    logger.error("Using ephemeral database")
    exit()

engine = create_engine(connection_string)


class Checkin(Base):
    __tablename__ = 'checkins'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())
    headers = Column(JSONB)
    payload = Column(JSONB)


def handler(request):
    headers = dict(request.headers())
    payload = request.json()
    checkin = Checkin(headers=headers, payload=payload)

    run_transaction(sessionmaker(bind=engine), lambda s: s.add(checkin))
    return flask.jsonify({
        "sleep": 10000,
        "fire": False
    })


if __name__ == "__main__":
    Base.metadata.create_all(engine)

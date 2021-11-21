import os
import logging
import uuid
import random

import flask
from sqlalchemy.engine import create_engine

from sqlalchemy import Column, CHAR, BOOLEAN, ForeignKey, select, BIGINT, update
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, TEXT
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy_cockroachdb import run_transaction

logging.basicConfig(level=logging.INFO)
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


def handler(request):
    is_valid, message = check_token(request)
    if not is_valid:
        return message, 404

    user: User = message.get("user")
    headers = dict(request.headers)
    payload = request.json
    checkin = Checkin(headers=headers, payload=payload)

    run_transaction(Session, lambda s: s.add(checkin))
    action_requests = payload.get("action_requests", [])
    action_updates = payload.get("action_updates", [])
    for action_request in action_requests:
        action = action_request.get("action", "noop")
        if action == "fire":
            action_obj = Action(
                username=user.username,
                action=action,
                duration=action_request.get("duration", 1000)
            )
            run_transaction(Session, lambda s: s.add(action_obj))
        else:
            logger.warning(f"skipping unrecognized action: {action}")

    for action_update in action_updates:
        try:
            id = uuid.UUID(action_update.get("id"))
            completed = action_update.get("completed", True)
        except ValueError as e:
            return {"error": str(e)}
        run_transaction(Session, lambda s: s.execute(update(Action).where(Action.id == id).values(completed=completed)))

    open_actions = []
    with Session() as session:
        actions = session.execute(
            select(Action).where(Action.username == user.username, Action.completed == False)
        ).scalars()
        open_actions += [
            {
                "id": str(action.id),
                "action": action.action,
                "duration": action.duration
            }
            for action in actions
        ]

    open_actions += [
            {
                "action": "sleep",
                "duration": random.randint(8, 12) * 1000
            }
        ]

    return flask.jsonify({
        "open_actions": open_actions
    })


def check_token(request):
    logger.debug("Getting authentication token")
    try:
        bearer = request.headers.get("Authorization")
        token = bearer.split()[1]
    except IndexError:
        return False, {
            "error": "unable to parse authorization token"
        }

    with Session() as session:
        try:
            user = session.execute(select(User).where(User.token == token)).scalar_one()
            return True, {"user": user}
        except (NoResultFound, MultipleResultsFound):
            return False, {"error": "unrecognized token"}


if __name__ == "__main__":
    Base.metadata.create_all(engine)

import logging
import uuid

from sqlalchemy import select, update, desc
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy_cockroachdb import run_transaction

from db import get_sessionmaker, User, Checkin, Action, CallbackDelay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_user(request):
    Session = get_sessionmaker()
    logger.debug("logging checkin")
    headers = dict(request.headers)
    payload = request.json
    checkin = Checkin(headers=headers, payload=payload)
    run_transaction(Session, lambda s: s.add(checkin))

    logger.debug("Getting authentication token")
    try:
        bearer = request.headers.get("Authorization")
        token = bearer.split()[1]
    except (IndexError, AttributeError):
        return {
            "error": "unable to parse authorization token"
        }, 404

    with Session() as session:
        try:
            user = session.execute(select(User).where(User.token == token)).scalar_one()
            request.user = user
        except (NoResultFound, MultipleResultsFound):
            return {"error": "unrecognized token"}, 404


def get_actions(request):
    Session = get_sessionmaker()
    include_completed: bool = bool(request.args.get("include_completed", False))
    include_all: bool = bool(request.args.get("include_all", False))
    conditions = []
    if not include_completed:
        conditions += [Action.completed == False]
    if not include_all:
        conditions += [Action.username == request.user.username]
    open_actions = []
    with Session() as session:
        actions = session.execute(
            select(Action).where(*conditions)
        ).scalars()
        open_actions += [
            {
                "id": str(action.id),
                "action": action.action,
                "duration": action.duration
            }
            for action in actions
        ]
        callback_delay = session.execute(select(CallbackDelay.interval).order_by(CallbackDelay.updated_at.desc()).limit(1)).scalar_one()

    return {
        "actions": open_actions,
        "delay": callback_delay
    }, 200


def create_action(request):
    Session = get_sessionmaker()
    action = request.json.get("action", "noop")
    if action == "fire":
        action_obj = Action(
            username=request.user.username,
            action=action,
            duration=request.json.get("duration", 1000)
        )
        run_transaction(Session, lambda s: s.add(action_obj))
    elif action == "update_callback_interval":
        new_interval = CallbackDelay(updated_by=request.user.username, interval=request.json.get("interval", 5*30*1000))
        run_transaction(Session, lambda s: s.add(new_interval))
    else:
        logger.warning(f"skipping unrecognized action: {action}")
    return {"status": "ok"}, 201


def update_action(request):
    Session = get_sessionmaker()
    id_: uuid = request.json.get("id", "")
    try:
        id_ = uuid.UUID(id_)
    except ValueError as e:
        return {"error": str(e)}, 500
    completed = request.json.get("completed", True)
    run_transaction(Session, lambda s: s.execute(update(Action).where(Action.id == id_).values(completed=completed)))
    return {"status": "ok"}, 200


def handler(request):
    load_user_error = load_user(request)
    if load_user_error is not None:
        return load_user_error
    if request.method == "GET":
        return get_actions(request)
    elif request.method == "POST":
        return create_action(request)
    elif request.method == "PUT":
        return update_action(request)
    return {"error": "unrecognized method"}, 500

import uuid

from flask import Flask, request
import pytest

from db import Action, init_db
from main import handler


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CONNECTION_STRING", "cockroachdb://root@localhost:26257/defaultdb")
    app = Flask("test_app")               # we don't really have an app. We just want request objects.
    with app.test_client() as client:
        with app.app_context():
            init_db(test_token="abcdefghijklmnopqrstuvwxyz0123456789abcd")
        yield client


def test_request(client):
    client.get("/gull-cannon")
    assert request.path == "/gull-cannon"


def test_auth(client):
    client.get("/gull-cannon/actions")
    res = handler(request)
    assert res[1] == 404


def test_get_actions(client):
    client.get("/gull-cannon/actions", headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"})
    res = handler(request)
    assert res[0] == {
        "actions": [],
        "delay": 5 * 60 * 1000
    }
    assert res[1] == 200


def test_add_action(client):
    client.post(
        "/gull-cannon/actions",
        headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"},
        json={"action": "fire", "duration": 2 * 60 * 1000},
    )
    res = handler(request)
    assert res[1] == 201
    assert res[0] == {
        "status": "ok",
    }
    client.get("/gull-cannon/actions", headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"})
    res = handler(request)
    assert res[0]["delay"] == 5 * 60 * 1000
    assert len(res[0]["actions"]) >= 1
    assert res[1] == 200


def test_complete_all_actions(client):
    client.get("/gull-cannon/actions", headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"})
    res = handler(request)
    for action in res[0]["actions"]:
        client.put(
            f"/gull-cannon/actions/{action['id']}",
            headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"},
            json={"id": action['id'], "completed": True},
        )
        handler(request)
    client.get("/gull-cannon/actions", headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"})
    res = handler(request)
    assert res[0]["delay"] == 5 * 60 * 1000
    assert len(res[0]["actions"]) == 0
    assert res[1] == 200


def test_update_callback(client):
    client.post("/gull-cannon/actions",
                headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"},
                json={"action": "update_callback_interval", "interval": 1000}
    )
    handler(request)
    client.get("/gull-cannon/actions", headers={"Authorization": "Bearer: abcdefghijklmnopqrstuvwxyz0123456789abcd"})
    res = handler(request)
    assert res[0]["delay"] == 1000
    assert res[1] == 200


def test_uuid():
    with pytest.raises(ValueError) as exc:
        _ = uuid.UUID("a;lkasdf")
    assert "badly formed hexadecimal UUID string" in str(exc.value)


def test_build_action():
    Action(username="james.p.campbell@gmail.com", action="fire", duration=1000)

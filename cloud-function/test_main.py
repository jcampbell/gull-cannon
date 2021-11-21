import uuid

import pytest
from sqlalchemy import select

from main import Session, Checkin, Action


def test_example():
    expected_id = uuid.UUID("4a91a4bc-d363-420b-b110-26bd74b9b9fa")
    with Session() as session:
        res = session.execute(
            select(Checkin).where(Checkin.id == expected_id)
        ).scalar_one()

    assert res.id == expected_id


def test_uuid():
    with pytest.raises(ValueError) as exc:
        _ = uuid.UUID("a;lkasdf")
    assert "badly formed hexadecimal UUID string" in str(exc.value)


def test_random():
    import random
    assert 8 <= random.randint(8, 12) <= 12


def test_build_action():
    Action(username="james.p.campbell@gmail.com", action="fire", duration=1000)

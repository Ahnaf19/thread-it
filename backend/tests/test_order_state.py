"""Pure order state-machine tests (ADR-0008) — no DB, just the legality rules."""

import pytest

from app.enums import OrderStatus
from app.order_state import (
    TERMINAL_STATUSES,
    IllegalTransition,
    assert_transition,
    can_transition,
)

P, PAID, FAIL, CANC, FUL = (
    OrderStatus.PENDING,
    OrderStatus.PAID,
    OrderStatus.FAILED,
    OrderStatus.CANCELLED,
    OrderStatus.FULFILLED,
)


@pytest.mark.parametrize("current,target", [(P, PAID), (P, FAIL), (P, CANC), (PAID, FUL)])
def test_legal_transitions_allowed(current, target):
    assert can_transition(current, target)
    assert_transition(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target",
    [
        (P, FUL),  # can't ship an unpaid order
        (PAID, P),  # no going back
        (PAID, FAIL),  # no reversing a cleared payment (refund is out of scope)
        (PAID, CANC),
        (CANC, PAID),
        (FAIL, PAID),
        (FUL, PAID),
        (FUL, P),
    ],
)
def test_illegal_transitions_rejected(current, target):
    assert not can_transition(current, target)
    with pytest.raises(IllegalTransition):
        assert_transition(current, target)


@pytest.mark.parametrize("status", [P, PAID, FAIL, CANC, FUL])
def test_same_status_is_idempotent_noop(status):
    assert can_transition(status, status)
    assert_transition(status, status)  # re-applying current status must not raise


def test_terminal_statuses_have_no_outgoing_transitions():
    for s in TERMINAL_STATUSES:
        assert all(not can_transition(s, t) for t in OrderStatus if t != s)


def test_terminal_set_is_exactly_failed_cancelled_fulfilled():
    assert TERMINAL_STATUSES == frozenset({FAIL, CANC, FUL})

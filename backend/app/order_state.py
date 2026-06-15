"""Order state machine — the legal-transition rules (ADR-0008).

Pure domain logic, no DB. Owns *legality* only: an illegal move raises, and
re-applying the current status is an idempotent no-op. *Idempotency against
duplicate/stale gateway callbacks* is a separate concern handled by the gateway
handlers' pending-status guard (see app/crud/checkout.py).
"""

from app.enums import OrderStatus

# From → set of statuses it may legally move to. Terminal statuses map to empty.
LEGAL_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING: frozenset(
        {OrderStatus.PAID, OrderStatus.FAILED, OrderStatus.CANCELLED}
    ),
    OrderStatus.PAID: frozenset({OrderStatus.FULFILLED}),
    OrderStatus.FAILED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.FULFILLED: frozenset(),
}

TERMINAL_STATUSES: frozenset[OrderStatus] = frozenset(
    status for status, exits in LEGAL_TRANSITIONS.items() if not exits
)


class IllegalTransition(Exception):
    """Raised when an order is asked to make a move outside the state machine."""

    def __init__(self, current: OrderStatus, target: OrderStatus):
        self.current = current
        self.target = target
        super().__init__(f"illegal order transition {current.value} -> {target.value}")


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    """True if the move is legal. Re-applying the current status is always allowed."""
    return target == current or target in LEGAL_TRANSITIONS[current]


def assert_transition(current: OrderStatus, target: OrderStatus) -> None:
    """Raise IllegalTransition unless the move is legal (or an idempotent no-op)."""
    if not can_transition(current, target):
        raise IllegalTransition(current, target)

from __future__ import annotations

from dataclasses import dataclass

from forex_trader.domain.models import Position


@dataclass(frozen=True)
class ReconcileResult:
    in_sync: bool
    reason: str
    broker_count: int
    expected_open: int


def reconcile_positions(
    *,
    broker_positions: list[Position],
    expected_open: int,
) -> ReconcileResult:
    """Compare the broker's open positions against the count we expect.

    The live loop refuses to open new trades when this disagrees, so it never
    acts on a stale or surprising view of the account.
    """
    broker_count = len(broker_positions)
    if broker_count == expected_open:
        return ReconcileResult(
            in_sync=True,
            reason="Broker and local state agree.",
            broker_count=broker_count,
            expected_open=expected_open,
        )
    return ReconcileResult(
        in_sync=False,
        reason=(
            f"Position mismatch: broker reports {broker_count} open, "
            f"local state expects {expected_open}."
        ),
        broker_count=broker_count,
        expected_open=expected_open,
    )

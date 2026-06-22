from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from forex_trader.broker.base import Broker
from forex_trader.domain.models import Candle, Quote
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.execution.reconcile import reconcile_positions
from forex_trader.market.sessions import DEFAULT_SESSION_TZ
from forex_trader.obs.logging import get_logger
from forex_trader.risk.policy import RiskPolicy
from forex_trader.safety.emergency import is_emergency_stopped
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.base import Strategy

logger = get_logger("live")


def make_oanda_fetch(
    *,
    broker: object,
    candle_source: Callable[[], list[Candle]],
) -> Callable[[], tuple[list[Candle], Quote, datetime]]:
    """Build a fetch() that pulls a live quote from the broker and recent
    candles from `candle_source` (e.g. fetch_oanda_candles bound to creds).

    Returns (candles, quote, now) where now is the quote's timestamp.
    """

    def fetch() -> tuple[list[Candle], Quote, datetime]:
        quote = broker.get_quote("EUR_USD")  # type: ignore[attr-defined]
        candles = candle_source()
        return candles, quote, quote.time

    return fetch


@dataclass(frozen=True)
class TickResult:
    status: str  # halted | out_of_sync | dry_run | ordered | blocked | no_signal
    reason: str


class LiveTrader:
    """A safety-gated single trading cycle for practice/live operation.

    Every tick: check the emergency stop, reconcile positions, then either
    place orders through the orchestrator (when armed) or evaluate the signal
    and risk without placing anything (dry run). All order placement still flows
    through the orchestrator's risk engine — there is no bypass.
    """

    def __init__(
        self,
        *,
        strategy: Strategy,
        risk_policy: RiskPolicy,
        broker: Broker,
        repository: TradingRepository,
        equity: float,
        armed: bool,
        emergency_stop_path: str,
        max_hold_minutes: int = 90,
        session_start_local: str = "05:00",
        session_end_local: str = "09:00",
        session_tz: str = DEFAULT_SESSION_TZ,
    ) -> None:
        self.armed = armed
        self.emergency_stop_path = emergency_stop_path
        self.strategy = strategy
        self.broker = broker
        self.session_start_local = session_start_local
        self.session_end_local = session_end_local
        self.session_tz = session_tz
        self.orchestrator = ExecutionOrchestrator(
            strategy=strategy,
            risk_policy=risk_policy,
            broker=broker,
            repository=repository,
            equity=equity,
            max_hold_minutes=max_hold_minutes,
            session_start_local=session_start_local,
            session_end_local=session_end_local,
            session_tz=session_tz,
        )

    def tick(self, *, candles: list[Candle], quote: Quote, now: datetime) -> TickResult:
        if is_emergency_stopped(self.emergency_stop_path):
            logger.warning("Emergency stop active; no action taken.")
            return TickResult(status="halted", reason="Emergency stop active.")

        expected_open = len(self.orchestrator.broker.list_open_positions())
        recon = reconcile_positions(
            broker_positions=self.broker.list_open_positions(),
            expected_open=expected_open,
        )
        if not recon.in_sync:
            logger.error("Reconciliation failed: %s", recon.reason)
            return TickResult(status="out_of_sync", reason=recon.reason)

        if not self.armed:
            # Evaluate the signal but place nothing. The orchestrator's risk
            # engine is never reached, so a dry run cannot move the account.
            signal = self.strategy.evaluate(candles, quote)
            detail = "signal present" if signal else "no signal"
            logger.info("Dry run tick: %s (no orders placed).", detail)
            return TickResult(status="dry_run", reason=f"Dry run — {detail}.")

        result = self.orchestrator.run_cycle(candles=candles, quote=quote, now=now)
        logger.info("Armed tick: %s — %s", result.status, result.reason)
        return TickResult(status=result.status, reason=result.reason)

    def run(
        self,
        *,
        max_iterations: int,
        sleep_seconds: float,
        fetch: Callable[[], tuple[list[Candle], Quote, datetime]],
    ) -> list[TickResult]:
        """Tick on an interval up to `max_iterations`, stopping on a halt.

        `fetch` returns the (candles, quote, now) for each tick — production
        wires this to OANDA pricing; tests inject deterministic data. The
        max-iterations guard means the loop can never run unbounded.
        """
        results: list[TickResult] = []
        for iteration in range(max_iterations):
            candles, quote, now = fetch()
            result = self.tick(candles=candles, quote=quote, now=now)
            results.append(result)
            if result.status == "halted":
                logger.warning("Loop stopping: emergency stop encountered.")
                break
            if iteration < max_iterations - 1 and sleep_seconds > 0:
                time.sleep(sleep_seconds)
        return results

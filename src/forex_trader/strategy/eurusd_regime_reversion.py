from __future__ import annotations

from forex_trader.analysis.regime import ReversionRegimeTracker
from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdRegimeReversionStrategy(Strategy):
    """Session-mean reversion, gated by a forecastable multi-day regime signal.

    The plain reversion edge is regime-dependent: it pays when the market has
    recently been mean-reverting and loses when it has been trending. Whether
    reversion paid over the trailing few days predicts the next day ~59-62% of
    the time, so this strategy only fades extension when the recent regime
    favors reversion. In a 12-month both-halves walk-forward this gating turned
    a losing half positive while preserving the winning half — the first rule in
    the search to survive that test.

    The strategy is stateful: it holds a ReversionRegimeTracker. The backtest /
    live loop feeds completed reversion outcomes back via
    observe_reversion_outcome so the regime read stays current. Deterministic —
    no LLM at runtime.
    """

    strategy_id = "eurusd_regime_reversion"

    def __init__(
        self,
        *,
        min_history: int = 6,
        extension_pips: float = 22.0,   # validated config (2yr 4-period walk-forward)
        target_fraction: float = 0.5,
        stop_pips: float = 12.0,
        max_spread_pips: float = 2.0,
        regime_window: int = 8,
        regime_threshold: float = 5.0,  # trade only in strongly-reverting regimes
        volume_mult: float = 1.2,        # require an elevated (exhaustion) volume
    ) -> None:
        self.min_history = min_history
        self.extension_pips = extension_pips
        self.target_fraction = target_fraction
        self.stop_pips = stop_pips
        self.max_spread_pips = max_spread_pips
        self.volume_mult = volume_mult
        self.required_history = min_history + 1
        self.regime = ReversionRegimeTracker(
            window=regime_window, favor_threshold=regime_threshold
        )
        # Pending observed extensions awaiting resolution: (deviation_sign,
        # entry_price, session_mean, target_price, stop_price, last_seen_time).
        # These let the strategy keep its regime read live by observing whether
        # extensions revert — even on bars where it does not trade — so it never
        # deadlocks itself.
        self._pending: list[dict[str, float]] = []
        self._last_obs_time: float | None = None

    def observe_reversion_outcome(self, pnl_pips: float) -> None:
        """No-op: the strategy now self-observes every extension in evaluate(),
        so it does not need executed-trade feedback from the runner (which would
        double-count and could deadlock when not trading)."""
        return None

    def _observe(self, candle: Candle, mean: float) -> None:
        """Resolve pending observed extensions against this candle and register
        a new one if the candle is itself an extension.

        This keeps the regime tracker learning from market behavior whether or
        not the strategy trades, so a quiet/unfavorable stretch cannot
        permanently starve the gate.
        """
        target_move_frac = self.target_fraction
        still_pending: list[dict[str, float]] = []
        for ext in self._pending:
            if ext["sign"] > 0:  # extended above mean -> reverts down
                if candle.low <= ext["target"]:
                    self.regime.record_outcome(ext["reward"])
                    continue
                if candle.high >= ext["stop"]:
                    self.regime.record_outcome(-self.stop_pips)
                    continue
            else:  # extended below mean -> reverts up
                if candle.high >= ext["target"]:
                    self.regime.record_outcome(ext["reward"])
                    continue
                if candle.low <= ext["stop"]:
                    self.regime.record_outcome(-self.stop_pips)
                    continue
            still_pending.append(ext)
        self._pending = still_pending

        deviation = (candle.close - mean) / PIP_SIZE
        if abs(deviation) >= self.extension_pips:
            move = abs(candle.close - mean) * target_move_frac
            sign = 1.0 if deviation > 0 else -1.0
            self._pending.append({
                "sign": sign,
                "reward": move / PIP_SIZE,
                "target": candle.close - move if sign > 0 else candle.close + move,
                "stop": candle.close + self.stop_pips * PIP_SIZE if sign > 0
                else candle.close - self.stop_pips * PIP_SIZE,
            })

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if len(candles) <= self.min_history:
            return None

        prior = candles[:-1]
        mean = sum(c.close for c in prior) / len(prior)
        latest_candle = candles[-1]
        # Observe market reversion behavior every bar to keep the regime live.
        self._observe(latest_candle, mean)

        if quote is None or quote.spread_pips > self.max_spread_pips:
            return None
        if not self.regime.reversion_favored():
            return None  # recent regime does not favor reversion — stand aside

        latest = latest_candle.close
        deviation_pips = (latest - mean) / PIP_SIZE
        if abs(deviation_pips) < self.extension_pips:
            return None

        # Volume gate: the extension must be a high-volume exhaustion spike.
        if self.volume_mult > 0:
            avg_volume = sum(c.volume for c in prior) / len(prior)
            if avg_volume <= 0 or latest_candle.volume < avg_volume * self.volume_mult:
                return None

        stop = self.stop_pips * PIP_SIZE
        target_move = abs(latest - mean) * self.target_fraction
        if deviation_pips > 0:
            return Signal(
                strategy_id=self.strategy_id, symbol=quote.symbol, side=OrderSide.SELL,
                entry_price=latest, stop_loss=latest + stop, take_profit=latest - target_move,
                reason="Faded extension above session mean (regime favors reversion).",
                metadata={"session_mean": mean, "deviation_pips": deviation_pips},
            )
        return Signal(
            strategy_id=self.strategy_id, symbol=quote.symbol, side=OrderSide.BUY,
            entry_price=latest, stop_loss=latest - stop, take_profit=latest + target_move,
            reason="Faded extension below session mean (regime favors reversion).",
            metadata={"session_mean": mean, "deviation_pips": deviation_pips},
        )

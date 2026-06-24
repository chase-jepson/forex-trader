from __future__ import annotations

from dataclasses import dataclass, field

from forex_trader.domain.enums import ResearchStatus


@dataclass(frozen=True)
class StrategyHypothesis:
    strategy_id: str
    summary: str
    required_inputs: list[str]
    risk_concerns: list[str]
    status: ResearchStatus = ResearchStatus.DRAFT

    @property
    def is_complete(self) -> bool:
        return bool(self.summary and self.required_inputs and self.risk_concerns)


@dataclass
class ResearchRegistry:
    hypotheses: dict[str, StrategyHypothesis] = field(default_factory=dict)

    @classmethod
    def with_default_hypotheses(cls) -> ResearchRegistry:
        registry = cls()
        registry.add_hypothesis(
            strategy_id="eurusd_opening_window",
            summary=(
                "Trade a confirmed breakout from a short opening range "
                "when spread is acceptable."
            ),
            required_inputs=["recent candles", "bid/ask quote", "spread", "session window"],
            risk_concerns=["false breakouts", "spread spikes", "stop too tight"],
            status=ResearchStatus.READY_FOR_SIM,
        )
        registry.add_hypothesis(
            strategy_id="eurusd_mean_reversion",
            summary="Fade overextended moves back toward a short-term average.",
            required_inputs=["recent candles", "volatility estimate", "trend filter"],
            risk_concerns=["strong trend continuation"],
            status=ResearchStatus.DRAFT,
        )
        registry.add_hypothesis(
            strategy_id="eurusd_news_avoidance",
            summary="Block trades around known high-impact macro events.",
            required_inputs=["economic calendar", "event severity", "session state"],
            risk_concerns=["incomplete or delayed event data"],
            status=ResearchStatus.DRAFT,
        )
        registry.add_hypothesis(
            strategy_id="eurusd_us_open_fade",
            summary=(
                "Fade a thrust beyond the opening range during the US open; "
                "evidence: 6mo of real data shows ~47% breakout follow-through "
                "(the window mean-reverts after a thrust)."
            ),
            required_inputs=["opening-range candles", "bid/ask quote", "spread"],
            risk_concerns=["strong trend days overrun the fade", "spread drag"],
            status=ResearchStatus.DRAFT,  # gated: must be validated before sim
        )
        registry.add_hypothesis(
            strategy_id="eurusd_vwap_reversion",
            summary=(
                "Fade extension from the running session mean during the US open. "
                "Evidence: when price extends >=20-30 pips from the session mean it "
                "reverts ~60%+ of the time. Walk-forward validated POSITIVE on both "
                "in-sample (+$147) and out-of-sample (+$41, 53% win) on 6mo real data."
            ),
            required_inputs=["session candles", "bid/ask quote", "spread"],
            risk_concerns=[
                "trend days that keep extending past the stop",
                "spread drag on a tight target",
                "small out-of-sample trade count",
            ],
            status=ResearchStatus.DRAFT,  # validated but awaiting user sign-off
        )
        return registry

    def add_hypothesis(
        self,
        strategy_id: str,
        summary: str,
        required_inputs: list[str],
        risk_concerns: list[str],
        status: ResearchStatus,
    ) -> None:
        self.hypotheses[strategy_id] = StrategyHypothesis(
            strategy_id=strategy_id,
            summary=summary,
            required_inputs=required_inputs,
            risk_concerns=risk_concerns,
            status=status,
        )

    def is_strategy_ready(self, strategy_id: str) -> bool:
        hypothesis = self.hypotheses.get(strategy_id)
        return bool(
            hypothesis
            and hypothesis.status == ResearchStatus.READY_FOR_SIM
            and hypothesis.is_complete
        )

    def ready_strategy_ids(self) -> list[str]:
        return [
            strategy_id
            for strategy_id in self.hypotheses
            if self.is_strategy_ready(strategy_id)
        ]

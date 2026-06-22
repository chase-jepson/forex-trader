from __future__ import annotations

from forex_trader.domain.models import RiskDecision, Signal


def explain_decision(signal: Signal | None, risk_decision: RiskDecision | None) -> str:
    if signal is None:
        return "No trade: no documented strategy rule fired."
    if risk_decision is None:
        return f"Signal only: {signal.reason}"
    verdict = "approved" if risk_decision.approved else "blocked"
    return f"Trade {verdict}: {signal.reason} Risk engine said: {risk_decision.reason}"


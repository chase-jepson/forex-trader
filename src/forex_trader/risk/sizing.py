from __future__ import annotations

from forex_trader.domain.models import PIP_VALUE_PER_UNIT


def calculate_units_for_risk(
    *,
    equity: float,
    max_risk_fraction: float,
    stop_loss_pips: float,
    pip_value_per_unit: float = PIP_VALUE_PER_UNIT,
) -> int:
    if equity <= 0:
        raise ValueError("equity must be positive")
    if max_risk_fraction <= 0:
        raise ValueError("max_risk_fraction must be positive")
    if stop_loss_pips <= 0:
        raise ValueError("stop_loss_pips must be positive")
    risk_amount = equity * max_risk_fraction
    risk_per_unit = stop_loss_pips * pip_value_per_unit
    return int(risk_amount / risk_per_unit)


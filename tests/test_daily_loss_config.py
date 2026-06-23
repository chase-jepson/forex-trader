"""Daily-loss cap is configurable; 0 disables it entirely."""
from forex_trader.risk.policy import RiskPolicy


def _validate(policy, daily_pnl):
    return policy.validate_trade(
        equity=10_000, open_positions=0, stop_loss_pips=10, take_profit=1.105,
        risk_amount=10, max_hold_minutes=90, daily_realized_pnl=daily_pnl,
    )


def test_cap_blocks_when_loss_exceeds_limit():
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)
    # -150 on 10k equity = 1.5% loss, exceeds the 1% cap.
    decision = _validate(policy, -150.0)
    assert decision.approved is False
    assert "daily loss" in decision.reason.lower()


def test_loose_cap_allows_a_moderate_loss():
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.20, max_open_positions=1)
    # -150 = 1.5%, well under a 20% cap.
    decision = _validate(policy, -150.0)
    assert decision.approved is True


def test_zero_cap_disables_the_limit_entirely():
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.0, max_open_positions=1)
    # Even a huge loss does not block when the cap is disabled.
    decision = _validate(policy, -9_999.0)
    assert decision.approved is True

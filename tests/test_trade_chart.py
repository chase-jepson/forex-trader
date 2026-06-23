"""Plotly candlestick chart for a trade story."""
from forex_trader.dashboard.trade_chart import build_trade_chart


def _view():
    return {
        "position_id": "pos-1", "side": "buy",
        "candles": [
            {"time": "2026-06-22T11:55:00+00:00", "open": 1.10, "high": 1.101,
             "low": 1.099, "close": 1.1005},
            {"time": "2026-06-22T11:56:00+00:00", "open": 1.1005, "high": 1.102,
             "low": 1.10, "close": 1.1015},
        ],
        "entry_price": 1.1016, "entry_time": "2026-06-22T12:00:00+00:00",
        "stop_loss": 1.0990, "take_profit": 1.1060,
        "exit_price": 1.1060, "exit_time": "2026-06-22T12:45:00+00:00",
        "is_closed": True, "outcome": "win",
    }


def test_chart_has_candlestick_and_level_lines():
    fig = build_trade_chart(_view())

    trace_types = {type(t).__name__ for t in fig.data}
    assert "Candlestick" in trace_types
    # Entry / exit markers present as scatter points.
    assert "Scatter" in trace_types
    # Stop and target rendered as horizontal lines (shapes).
    assert len(fig.layout.shapes) >= 2


def test_chart_handles_open_trade_without_exit():
    view = _view()
    view["is_closed"] = False
    view["exit_price"] = None
    view["exit_time"] = None

    fig = build_trade_chart(view)  # must not raise

    assert any(type(t).__name__ == "Candlestick" for t in fig.data)

from __future__ import annotations

from typing import Any


def build_story_view(story: dict[str, Any]) -> dict[str, Any]:
    """Turn a stored trade story into a chart-ready view model.

    Exposes the candle window, the entry/stop/target levels, the entry and exit
    markers, and a plain-English summary of why the trade was taken and how it
    ended — the data the trade explorer renders.
    """
    is_closed = story.get("closed_at") is not None
    return {
        "position_id": story["position_id"],
        "side": story["side"],
        "candles": story.get("context_candles", []),
        "entry_price": story["entry_price"],
        "entry_time": story["opened_at"],
        "stop_loss": story["stop_loss"],
        "take_profit": story["take_profit"],
        "exit_price": story.get("close_price"),
        "exit_time": story.get("closed_at"),
        "is_closed": is_closed,
        "is_dry_run": story.get("is_dry_run", False),
        "outcome": story.get("outcome", "open"),
        "pnl": story.get("pnl"),
        "summary": _summarize(story),
    }


def _summarize(story: dict[str, Any]) -> str:
    side = story["side"]
    reason = story.get("signal_reason", "")
    parts = [
        f"Took a {side} at {story['entry_price']:.5f} "
        f"(stop {story['stop_loss']:.5f}, target {story['take_profit']:.5f}). "
        f"Why: {reason}"
    ]
    if story.get("closed_at"):
        pnl = story.get("pnl")
        pnl_text = "" if pnl is None else f" for ${pnl:.2f}"
        parts.append(
            f"Closed via {story.get('exit_reason', 'exit')}{pnl_text} "
            f"({story.get('outcome', '')})."
        )
    else:
        parts.append("Still open.")
    return " ".join(parts)

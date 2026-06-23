from __future__ import annotations

from typing import Any


def render_live_market(st: Any, snapshot: dict[str, Any]) -> None:
    live = snapshot["live_market"]
    st.subheader("Live Market")
    left, right = st.columns(2)
    left.metric("Symbol", live.get("symbol") or "idle")
    right.metric("Latest status", live.get("latest_status", "idle"))
    st.json(live)


from __future__ import annotations

from typing import Any


def render_trade_reviews(st: Any, snapshot: dict[str, Any]) -> None:
    st.subheader("Trade Reviews")
    st.dataframe(snapshot["reviews"])


from __future__ import annotations

from typing import Any


def render_reports(st: Any, snapshot: dict[str, Any]) -> None:
    st.subheader("Reports")
    st.json(snapshot["reports"])

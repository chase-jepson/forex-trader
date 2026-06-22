from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast
from urllib import request

from forex_trader.broker.base import Broker
from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import OrderResult, Position, Quote, new_id


class OandaBroker(Broker):
    PRACTICE_URL = "https://api-fxpractice.oanda.com"
    LIVE_URL = "https://api-fxtrade.oanda.com"

    def __init__(self, *, mode: str, account_id: str, token: str) -> None:
        if mode not in {"practice", "live"}:
            raise ValueError("OANDA mode must be practice or live.")
        if not account_id or not token:
            raise ValueError("OANDA credentials are required for practice or live mode.")
        self.mode = mode
        self.account_id = account_id
        self.token = token
        self.base_url = self.PRACTICE_URL if mode == "practice" else self.LIVE_URL

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=10) as response:  # noqa: S310 - user-supplied broker URL is not accepted
            decoded = json.loads(response.read().decode("utf-8"))
        return cast(dict[str, Any], decoded)

    def get_quote(self, symbol: str) -> Quote:
        data = self._request("GET", f"/v3/accounts/{self.account_id}/pricing?instruments={symbol}")
        price = data["prices"][0]
        return Quote(
            symbol=symbol,
            bid=float(price["bids"][0]["price"]),
            ask=float(price["asks"][0]["price"]),
            time=datetime.fromisoformat(price["time"].replace("Z", "+00:00")),
        )

    def place_market_order(
        self,
        *,
        symbol: str,
        side: str | OrderSide,
        units: int,
        price: float,
        stop_loss: float,
        take_profit: float,
        opened_at: datetime | None = None,
    ) -> OrderResult:
        order_side = side if isinstance(side, OrderSide) else OrderSide(side)
        signed_units = units if order_side == OrderSide.BUY else -units
        payload = {
            "order": {
                "type": "MARKET",
                "instrument": symbol,
                "units": str(signed_units),
                "timeInForce": "FOK",
                "positionFill": "DEFAULT",
                "stopLossOnFill": {"price": f"{stop_loss:.5f}"},
                "takeProfitOnFill": {"price": f"{take_profit:.5f}"},
            }
        }
        data = self._request("POST", f"/v3/accounts/{self.account_id}/orders", payload)
        order_fill = data.get("orderFillTransaction", {})
        fill_price = float(order_fill.get("price", price))
        return OrderResult(
            order_id=str(order_fill.get("orderID", new_id("oanda-order"))),
            position_id=str(order_fill.get("id", new_id("oanda-pos"))),
            accepted=True,
            reason="OANDA order accepted.",
            symbol=symbol,
            side=order_side,
            units=units,
            fill_price=fill_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=opened_at or datetime.now(UTC),
        )

    def list_open_positions(self) -> list[Position]:
        data = self._request("GET", f"/v3/accounts/{self.account_id}/openPositions")
        positions: list[Position] = []
        for item in data.get("positions", []):
            long_units = int(float(item.get("long", {}).get("units", "0")))
            short_units = abs(int(float(item.get("short", {}).get("units", "0"))))
            if long_units:
                side = OrderSide.BUY
                units = long_units
                price = float(item["long"]["averagePrice"])
            elif short_units:
                side = OrderSide.SELL
                units = short_units
                price = float(item["short"]["averagePrice"])
            else:
                continue
            positions.append(
                Position(
                    position_id=item["instrument"],
                    symbol=item["instrument"],
                    side=side,
                    units=units,
                    entry_price=price,
                    stop_loss=0.0,
                    take_profit=0.0,
                    opened_at=datetime.now(UTC),
                )
            )
        return positions

    def close_position(
        self,
        position_id: str,
        price: float,
        closed_at: datetime | None = None,
    ) -> Position:
        payload = {"longUnits": "ALL", "shortUnits": "ALL"}
        data = self._request(
            "PUT",
            f"/v3/accounts/{self.account_id}/positions/{position_id}/close",
            payload,
        )
        fill = data.get("longOrderFillTransaction") or data.get("shortOrderFillTransaction") or {}
        close_price = float(fill.get("price", price))
        position = Position(
            position_id=position_id,
            symbol=position_id,
            side=OrderSide.BUY,
            units=0,
            entry_price=price,
            stop_loss=0.0,
            take_profit=0.0,
            opened_at=closed_at or datetime.now(UTC),
        )
        return position.close(price=close_price, closed_at=closed_at or datetime.now(UTC))

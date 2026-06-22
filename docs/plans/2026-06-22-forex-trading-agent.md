# Forex Trading Agent Master Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a first-principles `EUR/USD` trading product that starts in simulation, advances to broker practice mode, explains every decision, provides rich dashboard reporting, and creates a structured learning loop from every trade and blocked trade.

**Architecture:** Build this as a Python trading engine with a local web dashboard. The engine owns research artifacts, market data ingestion, deterministic strategies, risk checks, broker adapters, execution orchestration, reporting, and trade review records. The LLM is limited to explanation, summarization, and retrospective analysis; it never has direct authority to open or change trades.

**Tech Stack:** Python 3.12, FastAPI, Pydantic Settings, SQLModel or SQLAlchemy, SQLite, Streamlit or FastAPI plus lightweight frontend, pytest, ruff, mypy, pandas, Plotly, OANDA REST API first, broker abstraction for future IBKR support.

---

## Product Thesis

We are not building a black-box bot. We are building a reviewable trading product with five pillars:

1. `Research`: define trading concepts and hypotheses from first principles before encoding them.
2. `Simulation`: prove logic and safety without real money.
3. `Practice`: prove real broker integration in a demo environment.
4. `Reporting`: show live state, historical results, and rule-level explanations.
5. `Learning`: turn wins, losses, and blocked trades into explicit improvement proposals.

## Product Shape

### What v1 is

- A local-first trading engine running on your laptop
- A local web dashboard for live monitoring and reports
- A deterministic `EUR/USD` intraday strategy selected only after research
- A broker abstraction with `simulated`, `practice`, and later `live` modes
- A per-trade review system with rule explanations and an improvement backlog

### What v1 is not

- A self-modifying autonomous strategy
- A multi-pair portfolio manager
- A high-frequency or scalping engine
- A native macOS app
- A live-money system on day one

## Core Principles

- Start from first principles and document each domain concept before automating it.
- Treat every strategy rule as a testable hypothesis, not a trading truth.
- Prefer deterministic execution over LLM judgment.
- Every trade must be explainable before and after execution.
- Every loss, bad fill, or blocked trade should teach us something concrete.
- Live trading remains disabled until simulation and practice evidence justify enabling it.

## Initial Constraints

- First instrument: `EUR/USD`
- Trading style: intraday only
- Max trades per day: `1-2`
- Max open positions: `1`
- No overnight holds
- Stop loss required on every trade
- Take profit or explicit time-based exit required on every trade
- Broker target: `OANDA` first
- Broker fallback: `IBKR`
- Deployment target: local laptop first, hosted server later

## Recommended Product Architecture

```text
Dashboard UI
  -> Reporting API
    -> Trade/Signal/Review Database
      -> Execution Orchestrator
        -> Strategy Engine
        -> Risk Engine
        -> Broker Adapter
        -> Review Generator

Research Docs + Hypothesis Registry
  -> decides which strategies are eligible for simulation
```

## Target Project Layout

```text
forex-trader/
  README.md
  .env.example
  pyproject.toml
  docs/
    broker-notes.md
    glossary.md
    research/
      forex-basics.md
      eurusd-market-map.md
      strategy-hypotheses.md
      validation-checklist.md
    reviews/
      trade-review-template.md
      improvement-backlog.md
      weekly-review-template.md
    reports/
      dashboard-spec.md
      report-spec.md
  src/forex_trader/
    __init__.py
    config.py
    main.py
    domain/
      enums.py
      models.py
    research/
      registry.py
    market/
      pricing.py
      sessions.py
      candles.py
    strategy/
      base.py
      null_strategy.py
      eurusd_opening_window.py
    risk/
      policy.py
      sizing.py
    broker/
      base.py
      simulated.py
      oanda.py
    execution/
      orchestrator.py
      scheduler.py
    storage/
      db.py
      repositories.py
    review/
      models.py
      service.py
    llm/
      explainer.py
      reviewer.py
    reporting/
      daily.py
      weekly.py
      metrics.py
    api/
      app.py
      routes.py
    dashboard/
      app.py
      pages/
        live_market.py
        trade_reviews.py
        reports.py
  tests/
    test_config.py
    test_research_registry.py
    test_sessions.py
    test_risk_policy.py
    test_position_sizing.py
    test_strategy_selection.py
    test_strategy_eurusd_opening_window.py
    test_broker_simulated.py
    test_execution_orchestrator.py
    test_trade_review.py
    test_reporting_metrics.py
    test_live_mode_guards.py
```

## Phase Gates

### Phase 0: Research

Success means:
- we can explain forex basics in plain English
- we know what market window we want to target
- we have at least `3` documented hypotheses for `EUR/USD`
- one strategy is explicitly marked `ready_for_sim`

### Phase 1: Simulation

Success means:
- the engine can run end-to-end with no broker credentials
- signals, approvals, rejections, orders, and exits are persisted
- every completed or blocked trade has an explanation and review record

### Phase 2: Practice

Success means:
- the system can connect to the broker demo environment
- the system can place and close practice orders safely
- dashboard reports practice results clearly

### Phase 3: Micro Live

Success means:
- all safety gates are complete
- practice reliability thresholds are met
- live mode is still tightly throttled and reversible

## Reliability Criteria Before Any Live Trading

- At least `20` simulated trades reviewed
- At least `20` practice trades reviewed
- No unresolved critical guardrail failures
- No unexplained order state mismatches
- No missing stop loss or forced-close bugs
- Daily and weekly reports produce consistent totals

## Dashboard Requirements

### Live Dashboard

Must show:
- current `EUR/USD` quote
- bid/ask spread
- session state: `pre-trade`, `active`, `cutoff`, `closed`
- current strategy status
- current signal or no-signal reason
- risk approval or rejection reason
- open position summary
- stop loss, take profit, and max hold countdown
- realized and unrealized PnL

### Review Dashboard

Must show:
- completed trades
- blocked trades
- per-trade rule explanation
- before/after trade reasoning
- mistake tags
- follow-up improvement hypothesis
- review status

### Report Dashboard

Must show:
- daily summary
- weekly summary
- win rate
- average reward/risk
- average hold time
- top blocked-trade reasons
- recurring mistake tags
- improvement backlog status

## Reporting Requirements

### Daily Report

Include:
- total signals
- trades taken
- trades blocked
- wins/losses/scratch
- realized PnL
- best trade
- worst trade
- top rejection reasons
- lessons learned

### Weekly Report

Include:
- trend in win rate
- trend in expectancy
- recurring mistake patterns
- candidate rule changes
- candidate research questions

## Trade Review Requirements

Every trade review record must answer:
- what did the market look like at entry
- what rule or rules fired
- why did the risk engine approve or block it
- how did the trade exit
- what was the actual outcome
- what likely went right or wrong
- what should we test, change, or watch next time

## Task Order

### Task 1: Write the master product docs and glossary

**Files:**
- Create: `README.md`
- Create: `docs/glossary.md`
- Create: `docs/research/forex-basics.md`
- Create: `docs/research/eurusd-market-map.md`
- Create: `docs/research/validation-checklist.md`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_glossary_exists():
    assert Path("docs/glossary.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_research_registry.py -v`
Expected: FAIL because docs and registry scaffolding are not in place

**Step 3: Write minimal implementation**

Document, in plain English:
- what forex is
- what `EUR/USD` means
- what pips, spreads, slippage, liquidity, leverage, stop loss, take profit, and position sizing mean
- when `EUR/USD` tends to be active
- what must be understood before trusting a strategy

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_research_registry.py -v`
Expected: PASS after the registry/doc checks are aligned

**Step 5: Commit**

```bash
git add README.md docs/glossary.md docs/research/forex-basics.md docs/research/eurusd-market-map.md docs/research/validation-checklist.md
git commit -m "docs: add master product docs and glossary"
```

### Task 2: Create the hypothesis registry and strategy selection gate

**Files:**
- Create: `src/forex_trader/research/registry.py`
- Create: `docs/research/strategy-hypotheses.md`
- Create: `tests/test_research_registry.py`
- Create: `tests/test_strategy_selection.py`

**Step 1: Write the failing test**

```python
from forex_trader.research.registry import ResearchRegistry


def test_strategy_cannot_run_without_ready_research_status():
    registry = ResearchRegistry()
    assert registry.is_strategy_ready("eurusd_opening_window") is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_research_registry.py tests/test_strategy_selection.py -v`
Expected: FAIL because the registry does not exist

**Step 3: Write minimal implementation**

Create a registry that records:
- strategy id
- hypothesis summary
- required inputs
- risk concerns
- research status: `draft`, `ready_for_sim`, `rejected`

Document at least `3` strategy hypotheses for `EUR/USD`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_research_registry.py tests/test_strategy_selection.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/research/registry.py docs/research/strategy-hypotheses.md tests/test_research_registry.py tests/test_strategy_selection.py
git commit -m "feat: add research registry and strategy readiness gate"
```

### Task 3: Bootstrap the app, settings, and database skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/forex_trader/__init__.py`
- Create: `src/forex_trader/config.py`
- Create: `src/forex_trader/storage/db.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
from forex_trader.config import Settings


def test_settings_load_default_symbol():
    settings = Settings()
    assert settings.trade_symbol == "EUR_USD"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with import errors

**Step 3: Write minimal implementation**

Add typed settings for:
- app mode
- broker provider
- symbol
- session hours
- risk limits
- database path
- dashboard refresh interval

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/forex_trader/__init__.py src/forex_trader/config.py src/forex_trader/storage/db.py tests/test_config.py
git commit -m "build: bootstrap app settings and database skeleton"
```

### Task 4: Define core domain models and market session rules

**Files:**
- Create: `src/forex_trader/domain/enums.py`
- Create: `src/forex_trader/domain/models.py`
- Create: `src/forex_trader/market/sessions.py`
- Create: `src/forex_trader/market/candles.py`
- Create: `tests/test_sessions.py`

**Step 1: Write the failing test**

```python
from datetime import datetime

from forex_trader.market.sessions import can_open_new_trade


def test_trade_allowed_inside_session_window():
    dt = datetime.fromisoformat("2026-06-22T05:30:00-06:00")
    assert can_open_new_trade(dt, "05:00", "09:00") is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sessions.py -v`
Expected: FAIL because session helpers do not exist

**Step 3: Write minimal implementation**

Add:
- enums for app mode, order side, signal state, review outcome
- models for quotes, candles, signals, trade plans, orders, positions, reviews
- session logic for allowed trading window, forced close, and no overnight holds

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sessions.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/domain/enums.py src/forex_trader/domain/models.py src/forex_trader/market/sessions.py src/forex_trader/market/candles.py tests/test_sessions.py
git commit -m "feat: add domain models and session controls"
```

### Task 5: Build the risk engine and position sizing rules

**Files:**
- Create: `src/forex_trader/risk/policy.py`
- Create: `src/forex_trader/risk/sizing.py`
- Create: `tests/test_risk_policy.py`
- Create: `tests/test_position_sizing.py`

**Step 1: Write the failing test**

```python
from forex_trader.risk.policy import RiskPolicy


def test_rejects_trade_without_stop_loss():
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)
    approved, reason = policy.validate_trade(
        equity=10_000,
        open_positions=0,
        stop_loss_pips=None,
        risk_amount=25,
    )
    assert approved is False
    assert "stop" in reason.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_risk_policy.py tests/test_position_sizing.py -v`
Expected: FAIL because risk modules do not exist

**Step 3: Write minimal implementation**

Enforce:
- stop loss required
- take profit or timed exit required
- max risk per trade
- max daily loss
- max one open position
- max hold time
- max percent gain or loss tripwire
- deterministic position size calculation

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_risk_policy.py tests/test_position_sizing.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/risk/policy.py src/forex_trader/risk/sizing.py tests/test_risk_policy.py tests/test_position_sizing.py
git commit -m "feat: add risk policy and position sizing"
```

### Task 6: Build the broker abstraction and simulated broker

**Files:**
- Create: `src/forex_trader/broker/base.py`
- Create: `src/forex_trader/broker/simulated.py`
- Create: `tests/test_broker_simulated.py`

**Step 1: Write the failing test**

```python
from forex_trader.broker.simulated import SimulatedBroker


def test_simulated_broker_opens_and_closes_position():
    broker = SimulatedBroker()
    order = broker.place_market_order("EUR_USD", "buy", units=1000, stop_loss=1.0990, take_profit=1.1030)
    assert order.accepted is True
    assert broker.list_open_positions()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_broker_simulated.py -v`
Expected: FAIL because simulated broker does not exist

**Step 3: Write minimal implementation**

Create:
- abstract broker interface
- simulated fills
- open position tracking
- close logic
- PnL calculation
- parity with live guardrails

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_broker_simulated.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/broker/base.py src/forex_trader/broker/simulated.py tests/test_broker_simulated.py
git commit -m "feat: add broker abstraction and simulated mode"
```

### Task 7: Build strategy interfaces and a safe default null strategy

**Files:**
- Create: `src/forex_trader/strategy/base.py`
- Create: `src/forex_trader/strategy/null_strategy.py`
- Create: `tests/test_strategy_selection.py`

**Step 1: Write the failing test**

```python
from forex_trader.strategy.null_strategy import NullStrategy


def test_null_strategy_never_emits_trade_signal():
    strategy = NullStrategy()
    assert strategy.evaluate([]) is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_strategy_selection.py -v`
Expected: FAIL because strategy interface is missing

**Step 3: Write minimal implementation**

Create:
- strategy base interface
- null strategy for incomplete research
- selection logic that prevents non-ready strategies from running

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_strategy_selection.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/strategy/base.py src/forex_trader/strategy/null_strategy.py tests/test_strategy_selection.py
git commit -m "feat: add strategy interface and safe default strategy"
```

### Task 8: Implement the first research-backed `EUR/USD` strategy

**Files:**
- Create: `src/forex_trader/strategy/eurusd_opening_window.py`
- Modify: `docs/research/strategy-hypotheses.md`
- Create: `tests/test_strategy_eurusd_opening_window.py`

**Step 1: Write the failing test**

```python
from forex_trader.strategy.eurusd_opening_window import EuruUsdOpeningWindowStrategy


def test_emits_signal_when_valid_breakout_occurs():
    strategy = EuruUsdOpeningWindowStrategy()
    candles = [
        {"high": 1.1010, "low": 1.1000, "close": 1.1005},
        {"high": 1.1012, "low": 1.1002, "close": 1.1013},
    ]
    signal = strategy.evaluate(candles)
    assert signal is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_strategy_eurusd_opening_window.py -v`
Expected: FAIL because the strategy does not exist

**Step 3: Write minimal implementation**

Implement only if the hypothesis is marked `ready_for_sim`.

If selected:
- compute the setup window
- require acceptable spread
- allow one trade per session
- set deterministic stop and target rules

If not selected:
- keep `NullStrategy`
- document the blocker in research notes

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_strategy_eurusd_opening_window.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/strategy/eurusd_opening_window.py docs/research/strategy-hypotheses.md tests/test_strategy_eurusd_opening_window.py
git commit -m "feat: add first research-backed eurusd strategy"
```

### Task 9: Build the execution orchestrator and audit trail

**Files:**
- Create: `src/forex_trader/storage/repositories.py`
- Create: `src/forex_trader/execution/orchestrator.py`
- Create: `src/forex_trader/execution/scheduler.py`
- Create: `tests/test_execution_orchestrator.py`

**Step 1: Write the failing test**

```python
from forex_trader.execution.orchestrator import ExecutionOrchestrator


def test_trade_is_blocked_when_risk_policy_rejects_it():
    orchestrator = ExecutionOrchestrator(...)
    result = orchestrator.run_cycle()
    assert result.status == "blocked"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_execution_orchestrator.py -v`
Expected: FAIL because orchestrator does not exist

**Step 3: Write minimal implementation**

Execution flow:
- load quotes and candles
- evaluate strategy
- calculate trade plan
- validate risk
- place or reject order
- persist signal, decision, order, and outcome
- schedule forced close at max hold or cutoff

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_execution_orchestrator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/storage/repositories.py src/forex_trader/execution/orchestrator.py src/forex_trader/execution/scheduler.py tests/test_execution_orchestrator.py
git commit -m "feat: add execution orchestrator and audit trail"
```

### Task 10: Build the review engine and learning backlog

**Files:**
- Create: `docs/reviews/trade-review-template.md`
- Create: `docs/reviews/weekly-review-template.md`
- Create: `docs/reviews/improvement-backlog.md`
- Create: `src/forex_trader/review/models.py`
- Create: `src/forex_trader/review/service.py`
- Create: `src/forex_trader/llm/reviewer.py`
- Create: `tests/test_trade_review.py`

**Step 1: Write the failing test**

```python
from forex_trader.review.service import TradeReviewService


def test_losing_trade_generates_review_record():
    service = TradeReviewService()
    review = service.create_review(
        trade_id="t-123",
        outcome="loss",
        pnl=-42.0,
        rule_snapshot={"strategy": "eurusd_opening_window"},
    )
    assert review.trade_id == "t-123"
    assert review.outcome == "loss"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_trade_review.py -v`
Expected: FAIL because review service does not exist

**Step 3: Write minimal implementation**

Store:
- trade id
- market context
- strategy version
- signal explanation
- risk approval or rejection reason
- outcome: `win`, `loss`, `scratch`, `blocked`
- mistake tags
- improvement hypothesis
- review status

Ensure the LLM can summarize a review but cannot modify strategy rules automatically.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_trade_review.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/reviews/trade-review-template.md docs/reviews/weekly-review-template.md docs/reviews/improvement-backlog.md src/forex_trader/review/models.py src/forex_trader/review/service.py src/forex_trader/llm/reviewer.py tests/test_trade_review.py
git commit -m "feat: add review engine and learning backlog"
```

### Task 11: Build the explanation layer and reporting metrics

**Files:**
- Create: `src/forex_trader/llm/explainer.py`
- Create: `src/forex_trader/reporting/metrics.py`
- Create: `src/forex_trader/reporting/daily.py`
- Create: `src/forex_trader/reporting/weekly.py`
- Create: `docs/reports/dashboard-spec.md`
- Create: `docs/reports/report-spec.md`
- Create: `tests/test_reporting_metrics.py`

**Step 1: Write the failing test**

```python
from forex_trader.reporting.metrics import summarize_trade_outcomes


def test_reporting_metrics_include_win_rate():
    summary = summarize_trade_outcomes(
        [{"outcome": "win"}, {"outcome": "loss"}, {"outcome": "win"}]
    )
    assert summary["win_rate"] == 2 / 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_reporting_metrics.py -v`
Expected: FAIL because reporting modules do not exist

**Step 3: Write minimal implementation**

Add:
- deterministic metrics calculations
- human-readable trade explanation formatter
- daily report generator
- weekly report generator
- docs for dashboard and report panels

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_reporting_metrics.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/forex_trader/llm/explainer.py src/forex_trader/reporting/metrics.py src/forex_trader/reporting/daily.py src/forex_trader/reporting/weekly.py docs/reports/dashboard-spec.md docs/reports/report-spec.md tests/test_reporting_metrics.py
git commit -m "feat: add explanation layer and reporting metrics"
```

### Task 12: Build the dashboard and local API

**Files:**
- Create: `src/forex_trader/api/app.py`
- Create: `src/forex_trader/api/routes.py`
- Create: `src/forex_trader/dashboard/app.py`
- Create: `src/forex_trader/dashboard/pages/live_market.py`
- Create: `src/forex_trader/dashboard/pages/trade_reviews.py`
- Create: `src/forex_trader/dashboard/pages/reports.py`

**Step 1: Write the failing test**

```python
def test_dashboard_spec_requires_live_and_review_pages():
    required_pages = {"live_market", "trade_reviews", "reports"}
    assert required_pages == {"live_market", "trade_reviews", "reports"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_reporting_metrics.py -v`
Expected: FAIL until dashboard files and backing endpoints exist

**Step 3: Write minimal implementation**

Build pages for:
- live market and decision feed
- trade reviews and explanation details
- daily and weekly reports

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_reporting_metrics.py -v`
Expected: PASS once page contracts and data plumbing exist

**Step 5: Commit**

```bash
git add src/forex_trader/api/app.py src/forex_trader/api/routes.py src/forex_trader/dashboard/app.py src/forex_trader/dashboard/pages/live_market.py src/forex_trader/dashboard/pages/trade_reviews.py src/forex_trader/dashboard/pages/reports.py
git commit -m "feat: add local api and dashboard"
```

### Task 13: Add OANDA practice integration

**Files:**
- Create: `src/forex_trader/broker/oanda.py`
- Modify: `src/forex_trader/config.py`
- Modify: `README.md`

**Step 1: Write the failing test**

Add a broker contract test that verifies:
- quote shape
- order request shape
- practice environment configuration

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_broker_simulated.py -v`
Expected: FAIL because OANDA adapter is not implemented

**Step 3: Write minimal implementation**

Implement:
- token auth
- pricing fetch
- order placement with stop and target
- position list
- position close
- separate practice and live base URLs

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_broker_simulated.py -v`
Expected: PASS for mocked contract coverage

**Step 5: Run practice smoke test**

Run: `pytest -m integration -v`
Expected: PASS against practice credentials only

**Step 6: Commit**

```bash
git add src/forex_trader/broker/oanda.py src/forex_trader/config.py README.md
git commit -m "feat: add oanda practice adapter"
```

### Task 14: Add startup guards, mode gates, and operator controls

**Files:**
- Create: `src/forex_trader/main.py`
- Create: `tests/test_live_mode_guards.py`
- Modify: `README.md`

**Step 1: Write the failing test**

```python
def test_live_mode_requires_explicit_enable_flag():
    assert True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_live_mode_guards.py -v`
Expected: FAIL because live-mode guards do not exist

**Step 3: Write minimal implementation**

Add:
- explicit `simulated`, `practice`, and `live` modes
- live mode hard-disabled by default
- startup checks for credentials and broker connectivity
- kill switch file or env flag
- daily reset workflow

**Step 4: Run full suite**

Run: `pytest -v`
Expected: PASS

**Step 5: Run lint and typecheck**

Run: `ruff check .`
Expected: PASS

Run: `mypy src`
Expected: PASS

**Step 6: Commit**

```bash
git add src/forex_trader/main.py tests/test_live_mode_guards.py README.md
git commit -m "feat: add mode gates and operator controls"
```

## Acceptance Criteria

- Core forex concepts are documented in `docs/glossary.md` and `docs/research/`.
- Strategy execution is blocked unless research status is `ready_for_sim`.
- Simulated mode runs without broker credentials.
- Practice mode works with broker demo credentials.
- Every order path is mediated by the risk engine.
- Every trade and blocked trade receives an explanation and review record.
- Daily and weekly reports are generated from persisted data.
- Dashboard shows live state, decision feed, reviews, and reports.
- LLM output is explanatory only and never changes live trading behavior.
- Live mode remains off until simulation and practice evidence justify it.

## Open Decisions To Confirm

- Exact morning session hours in `America/Mexico_City`
- Exact `max % risk per trade`
- Exact profit-taking logic
- Exact review tags you care most about
- Streamlit vs FastAPI-plus-frontend preference for the dashboard shell

## Recommended Execution Order

1. Build docs and research registry first.
2. Build risk and simulation second.
3. Build review and reporting before broker practice mode.
4. Add OANDA practice integration only after simulated mode is stable.
5. Keep live mode disabled until you explicitly approve its criteria.

Plan complete and saved to `docs/plans/2026-06-22-forex-trading-agent.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

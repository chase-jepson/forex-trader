from pathlib import Path

from forex_trader.research.registry import ResearchRegistry, ResearchStatus


def test_research_docs_exist_for_beginner_foundation():
    required_docs = [
        Path("README.md"),
        Path("docs/glossary.md"),
        Path("docs/research/forex-basics.md"),
        Path("docs/research/eurusd-market-map.md"),
        Path("docs/research/strategy-hypotheses.md"),
        Path("docs/research/validation-checklist.md"),
    ]

    missing = [str(path) for path in required_docs if not path.exists()]

    assert missing == []


def test_strategy_cannot_be_ready_without_required_research_fields():
    registry = ResearchRegistry()
    registry.add_hypothesis(
        strategy_id="incomplete",
        summary="Breakout idea with missing inputs.",
        required_inputs=[],
        risk_concerns=["False breakouts"],
        status=ResearchStatus.READY_FOR_SIM,
    )

    assert registry.is_strategy_ready("incomplete") is False


def test_default_registry_has_one_ready_eurusd_strategy():
    registry = ResearchRegistry.with_default_hypotheses()

    assert registry.is_strategy_ready("eurusd_opening_window") is True
    assert registry.ready_strategy_ids() == ["eurusd_opening_window"]


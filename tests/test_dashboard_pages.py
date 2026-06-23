def test_dashboard_section_modules_expose_render_functions():
    from forex_trader.dashboard.sections.live_market import render_live_market
    from forex_trader.dashboard.sections.reports import render_reports
    from forex_trader.dashboard.sections.trade_reviews import render_trade_reviews

    assert callable(render_live_market)
    assert callable(render_reports)
    assert callable(render_trade_reviews)

def test_dashboard_page_modules_expose_render_functions():
    from forex_trader.dashboard.pages.live_market import render_live_market
    from forex_trader.dashboard.pages.reports import render_reports
    from forex_trader.dashboard.pages.trade_reviews import render_trade_reviews

    assert callable(render_live_market)
    assert callable(render_reports)
    assert callable(render_trade_reviews)


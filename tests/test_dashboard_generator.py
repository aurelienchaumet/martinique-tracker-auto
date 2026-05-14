from core.price_store import PriceRecord
from dashboard.generator import generate_dashboard


def _records():
    return [
        PriceRecord("2026-10-01T08:00:00", "Air Caraïbes", "2026-12-28", "2027-01-15", 487.0),
        PriceRecord("2026-10-01T14:00:00", "Air Caraïbes", "2026-12-28", "2027-01-15", 465.0),
        PriceRecord("2026-10-01T08:00:00", "Corsair", "2026-12-28", "2027-01-15", 399.0),
        PriceRecord("2026-10-01T08:00:00", "Air France", "2026-12-29", "2027-01-16", 550.0),
    ]


def test_generate_returns_html_string():
    html = generate_dashboard(_records())
    assert isinstance(html, str)
    assert "<!DOCTYPE html" in html


def test_dashboard_contains_chart_js():
    html = generate_dashboard(_records())
    assert "chart.js" in html.lower() or "Chart" in html


def test_dashboard_contains_airline_names():
    html = generate_dashboard(_records())
    assert "Air Caraïbes" in html
    assert "Corsair" in html
    assert "Air France" in html


def test_dashboard_contains_price_data():
    html = generate_dashboard(_records())
    assert "487" in html
    assert "399" in html


def test_dashboard_contains_all_route_combos():
    html = generate_dashboard(_records())
    assert "2026-12-28" in html
    assert "2027-01-15" in html
    assert "2026-12-29" in html
    assert "2027-01-16" in html


def test_dashboard_shows_last_updated():
    html = generate_dashboard(_records())
    assert "Mis à jour" in html or "mise à jour" in html.lower()

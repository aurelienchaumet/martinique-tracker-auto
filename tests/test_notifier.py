import pytest
from core.alert_engine import Alert
from core.notifier import build_email_html, build_subject, generate_pdf_bytes


def _alert(airline, delta):
    old = 500.0
    new = old + delta
    return Alert(
        airline=airline,
        outbound="2026-12-28",
        return_date="2027-01-15",
        old_price=old,
        new_price=new,
    )


def test_subject_drop():
    alert = _alert("Air Caraïbes", -45.0)
    subject = build_subject(alert)
    assert "CHUTE" in subject
    assert "45" in subject
    assert "Air Caraïbes" in subject


def test_subject_rise():
    alert = _alert("Corsair", 30.0)
    subject = build_subject(alert)
    assert "HAUSSE" in subject
    assert "30" in subject


def test_email_html_contains_prices():
    alert = _alert("Air France", -25.0)
    html = build_email_html([alert])
    assert "Air France" in html
    assert "500" in html
    assert "475" in html


def test_email_html_is_valid_html():
    alert = _alert("Corsair", 22.0)
    html = build_email_html([alert])
    assert html.strip().startswith("<!DOCTYPE html")
    assert "</html>" in html


def test_generate_pdf_bytes_returns_bytes():
    from core.price_store import PriceRecord
    records = [
        PriceRecord(
            timestamp="2026-10-01T08:00:00",
            airline="Air Caraïbes",
            outbound="2026-12-28",
            return_date="2027-01-15",
            price=487.0,
        )
    ]
    pdf = generate_pdf_bytes(records)
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100

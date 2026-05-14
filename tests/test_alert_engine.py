import pytest
from core.price_store import PriceRecord
from core.alert_engine import Alert, detect_alert


def _record(airline, outbound, return_date, price, ts="2026-10-01T08:00:00"):
    return PriceRecord(
        timestamp=ts,
        airline=airline,
        outbound=outbound,
        return_date=return_date,
        price=price,
    )


def test_no_alert_on_first_record():
    records = []
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)
    assert alert is None


def test_no_alert_below_threshold():
    records = [_record("Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)]
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 500.0)
    assert alert is None


def test_alert_on_drop():
    records = [_record("Corsair", "2026-12-28", "2027-01-15", 450.0)]
    alert = detect_alert(records, "Corsair", "2026-12-28", "2027-01-15", 410.0)
    assert alert is not None
    assert alert.is_drop is True
    assert alert.delta == pytest.approx(-40.0)


def test_alert_on_rise():
    records = [_record("Air France", "2026-12-29", "2027-01-16", 500.0)]
    alert = detect_alert(records, "Air France", "2026-12-29", "2027-01-16", 530.0)
    assert alert is not None
    assert alert.is_drop is False
    assert alert.delta == pytest.approx(30.0)


def test_alert_exact_threshold_no_trigger():
    records = [_record("Corsair", "2026-12-28", "2027-01-15", 450.0)]
    alert = detect_alert(records, "Corsair", "2026-12-28", "2027-01-15", 470.0)
    assert alert is None


def test_alert_label_drop():
    records = [_record("Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)]
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 440.0)
    assert "↓" in alert.label
    assert "47" in alert.label


def test_alert_label_rise():
    records = [_record("Air Caraïbes", "2026-12-28", "2027-01-15", 440.0)]
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)
    assert "↑" in alert.label

import json
import pytest
from pathlib import Path
from core.price_store import (
    PriceRecord,
    load_prices,
    save_prices,
    append_price,
    get_last_price,
)


@pytest.fixture
def tmp_prices_path(tmp_path, monkeypatch):
    p = tmp_path / "prices.json"
    p.write_text("[]")
    monkeypatch.setattr("core.price_store.DATA_PATH", p)
    return p


def test_load_empty(tmp_prices_path):
    assert load_prices() == []


def test_save_and_load(tmp_prices_path):
    records = [
        PriceRecord(
            timestamp="2026-10-01T08:00:00",
            airline="Air Caraïbes",
            outbound="2026-12-28",
            return_date="2027-01-15",
            price=487.0,
        )
    ]
    save_prices(records)
    loaded = load_prices()
    assert len(loaded) == 1
    assert loaded[0].price == 487.0
    assert loaded[0].airline == "Air Caraïbes"


def test_append_price(tmp_prices_path):
    append_price("Corsair", "2026-12-28", "2027-01-15", 399.0)
    append_price("Corsair", "2026-12-28", "2027-01-15", 410.0)
    records = load_prices()
    assert len(records) == 2
    assert records[-1].price == 410.0


def test_get_last_price_found(tmp_prices_path):
    append_price("Air France", "2026-12-29", "2027-01-16", 520.0)
    append_price("Air France", "2026-12-29", "2027-01-16", 505.0)
    records = load_prices()
    last = get_last_price(records, "Air France", "2026-12-29", "2027-01-16")
    assert last == 505.0


def test_get_last_price_not_found(tmp_prices_path):
    records = load_prices()
    assert get_last_price(records, "Air France", "2026-12-29", "2027-01-16") is None


def test_get_last_price_ignores_other_airlines(tmp_prices_path):
    append_price("Corsair", "2026-12-28", "2027-01-15", 350.0)
    records = load_prices()
    assert get_last_price(records, "Air France", "2026-12-28", "2027-01-15") is None

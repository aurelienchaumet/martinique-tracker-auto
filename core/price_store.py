import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DATA_PATH = Path(__file__).parent.parent / "data" / "prices.json"


@dataclass
class PriceRecord:
    timestamp: str
    airline: str
    outbound: str
    return_date: str
    price: float
    currency: str = "EUR"


def load_prices() -> List[PriceRecord]:
    if not DATA_PATH.exists():
        return []
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[price_store] WARNING: prices.json is corrupted ({e}), returning empty list")
        return []
    return [PriceRecord(**r) for r in data]


def save_prices(records: List[PriceRecord]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2, ensure_ascii=False)


def append_price(airline: str, outbound: str, return_date: str, price: float) -> None:
    records = load_prices()
    records.append(
        PriceRecord(
            timestamp=datetime.now().isoformat(),
            airline=airline,
            outbound=outbound,
            return_date=return_date,
            price=price,
        )
    )
    save_prices(records)


def get_last_price(
    records: List[PriceRecord], airline: str, outbound: str, return_date: str
) -> Optional[float]:
    """Return the most recent price for the given combination.

    Records are sorted by timestamp so the result is correct even if the
    caller passes records out of insertion order.
    """
    matches = [
        r
        for r in records
        if r.airline == airline
        and r.outbound == outbound
        and r.return_date == return_date
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda r: r.timestamp)[-1].price

from dataclasses import dataclass
from typing import List, Optional

from config import ALERT_THRESHOLD
from core.price_store import PriceRecord, get_last_price


@dataclass
class Alert:
    airline: str
    outbound: str
    return_date: str
    old_price: float
    new_price: float

    @property
    def delta(self) -> float:
        return self.new_price - self.old_price

    @property
    def is_drop(self) -> bool:
        return self.delta < 0

    @property
    def label(self) -> str:
        sign = "↓" if self.is_drop else "↑"
        return f"{sign} {abs(self.delta):.0f}€"


def detect_alert(
    records: List[PriceRecord],
    airline: str,
    outbound: str,
    return_date: str,
    new_price: float,
    threshold: float = ALERT_THRESHOLD,
) -> Optional[Alert]:
    last = get_last_price(records, airline, outbound, return_date)
    if last is None:
        return None
    if abs(new_price - last) > threshold:
        return Alert(
            airline=airline,
            outbound=outbound,
            return_date=return_date,
            old_price=last,
            new_price=new_price,
        )
    return None

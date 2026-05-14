import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional

from playwright.async_api import Page


class AirlineScraper(ABC):
    name: str = ""

    async def get_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        try:
            return await self._fetch_price(page, outbound, return_date)
        except Exception as e:
            print(f"[{self.name}] Error ({outbound} → {return_date}): {e}")
            return None

    @abstractmethod
    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        pass

    def _parse_price(self, text: str) -> Optional[float]:
        import re
        # Remove everything except digits, comma, period, space
        cleaned = re.sub(r"[^\d\s,.]", "", text.strip())
        # Remove spaces (thousand separators), replace comma with period
        cleaned = cleaned.replace(" ", "").replace(",", ".")
        # Remove trailing/leading periods
        cleaned = cleaned.strip(".")
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    async def _random_delay(self):
        await asyncio.sleep(random.uniform(2.0, 5.0))

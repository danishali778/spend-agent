from __future__ import annotations

import re

from app.schemas.domain import MoneyAmount

DATE_PATTERNS = (
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b"),
    re.compile(r"\b([A-Z][a-z]+ \d{1,2})\b"),
)
MONEY_PATTERN = re.compile(
    r"(?P<raw>(?:(?P<currency>USD)\s*)?(?P<value>\$\d[\d,]*(?:\.\d{1,2})?|\d[\d,]*,\d{3}(?:\.\d{1,2})?))"
)


def extract_iso_dates(text: str) -> list[str]:
    results: list[str] = []
    for pattern in DATE_PATTERNS:
        results.extend(match.group(1) for match in pattern.finditer(text))
    return list(dict.fromkeys(results))


def extract_money_amounts(text: str) -> list[MoneyAmount]:
    amounts: list[MoneyAmount] = []
    for match in MONEY_PATTERN.finditer(text):
        currency = match.group("currency")
        numeric_value = match.group("value")
        normalized = numeric_value.replace("$", "").replace(",", "")
        amounts.append(
            MoneyAmount(
                currency=currency or ("USD" if "$" in numeric_value else None),
                amount=float(normalized),
                raw=match.group("raw"),
            )
        )
    return amounts

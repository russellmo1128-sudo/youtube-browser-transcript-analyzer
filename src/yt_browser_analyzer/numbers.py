from __future__ import annotations

import re


_COMPACT_SUFFIXES = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
    "พัน": 1_000,
    "หมื่น": 10_000,
    "แสน": 100_000,
    "ล้าน": 1_000_000,
    "万": 10_000,
    "萬": 10_000,
    "亿": 100_000_000,
    "億": 100_000_000,
}


def parse_count_text(value: str | None) -> int | None:
    """Best-effort parser for public YouTube count text.

    The raw text is always more trustworthy than this parsed number because
    YouTube localizes and abbreviates counts.
    """

    if not value:
        return None
    text = value.strip().replace(",", "")
    if not text:
        return None

    for suffix, multiplier in _COMPACT_SUFFIXES.items():
        match = re.search(r"(\d+(?:\.\d+)?)\s*" + re.escape(suffix), text, re.IGNORECASE)
        if match:
            return int(float(match.group(1)) * multiplier)

    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = match.group(0)
    if "." in number:
        return int(float(number))
    return int(number)

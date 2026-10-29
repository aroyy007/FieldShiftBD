"""Conservative Bengali language helpers for farm-scoped chat.

These helpers normalize only values that have an unambiguous, locally supported
form. They do not infer a date from the Bengali word ``কাল`` because it can
mean either yesterday or tomorrow depending on context.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_NUMBER_WORDS = {
    "শূন্য": 0,
    "এক": 1,
    "একটি": 1,
    "একটা": 1,
    "দুই": 2,
    "দু": 2,
    "দুটি": 2,
    "তিন": 3,
    "চার": 4,
    "পাঁচ": 5,
    "ছয়": 6,
    "ছয়": 6,
    "সাত": 7,
    "আট": 8,
    "নয়": 9,
    "নয়": 9,
    "দশ": 10,
    "এগারো": 11,
    "বারো": 12,
    "তেরো": 13,
    "চৌদ্দ": 14,
    "পনেরো": 15,
    "ষোলো": 16,
    "সতেরো": 17,
    "আঠারো": 18,
    "উনিশ": 19,
    "বিশ": 20,
    "একুশ": 21,
    "বাইশ": 22,
    "তেইশ": 23,
    "চব্বিশ": 24,
    "পঁচিশ": 25,
    "ছাব্বিশ": 26,
    "সাতাশ": 27,
    "আটাশ": 28,
    "উনত্রিশ": 29,
    "ত্রিশ": 30,
    "চল্লিশ": 40,
    "পঞ্চাশ": 50,
    "ষাট": 60,
    "সত্তর": 70,
    "আশি": 80,
    "নব্বই": 90,
    "একশ": 100,
    "একশো": 100,
    "একশত": 100,
    "দেড়": 1.5,
    "দেড়": 1.5,
    "আধা": 0.5,
}

_UNIT_ALIASES = {
    "kg": ("kg", "কেজি", "কিলোগ্রাম", "কিলোগ্রামস"),
    "g": ("g", "গ্রাম", "গ্রামস"),
    "L": ("l", "liter", "litre", "লিটার", "লি"),
    "mm": ("mm", "মিমি", "মিলিমিটার"),
    "cm": ("cm", "সেমি", "সেন্টিমিটার"),
    "m": ("m", "মিটার"),
    "°C": ("°c", "celsius", "ডিগ্রি সেলসিয়াস", "ডিগ্রি সেলসিয়াস", "সেলসিয়াস", "সেলসিয়াস"),
    "acre": ("acre", "acres", "একর"),
    "bigha": ("bigha", "বিঘা"),
    "maund": ("maund", "মন", "মণ"),
}


def normalize_bengali_digits(value: str) -> str:
    """Convert Bengali digits to ASCII digits while preserving other text."""

    return value.translate(_DIGITS)


def parse_bangla_number(value: str) -> int | float | None:
    """Parse a single common Bengali number or digit sequence; never guess."""

    text = normalize_bengali_digits(value).strip().casefold()
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        number = float(text) if "." in text else int(text)
        return int(number) if isinstance(number, float) and number.is_integer() else number
    return _NUMBER_WORDS.get(text)


def parse_bangla_date(value: str, *, today: date | None = None) -> date | None:
    """Parse explicit ISO/day-month-year dates and unambiguous Bengali relative dates."""

    text = normalize_bengali_digits(value).strip().casefold()
    reference = today or datetime.now(ZoneInfo("Asia/Dhaka")).date()

    for pattern, order in (
        (r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", "ymd"),
        (r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})(?!\d)", "dmy"),
    ):
        match = re.search(pattern, text)
        if not match:
            continue
        parts = [int(part) for part in match.groups()]
        year, month, day_value = parts if order == "ymd" else (parts[2], parts[1], parts[0])
        try:
            return date(year, month, day_value)
        except ValueError:
            return None

    if re.search(r"আগামী\s*পরশু", text):
        return reference + timedelta(days=2)
    if re.search(r"আগামী\s*কাল(?:কে)?", text):
        return reference + timedelta(days=1)
    if re.search(r"গত\s*পরশু", text):
        return reference - timedelta(days=2)
    if re.search(r"গত\s*কাল(?:কে)?", text):
        return reference - timedelta(days=1)
    if re.search(r"(?<!\S)(?:আজ|আজকে)(?!\S)", text):
        return reference
    if re.search(r"(?<!\S)পরশু(?!\S)", text):
        return reference + timedelta(days=2)

    day_count = re.search(r"(?<!\S)([\w০-৯]+)\s+দিন\s*(?:পর|পরে)(?!\S)", text)
    if day_count:
        days = parse_bangla_number(day_count.group(1))
        if isinstance(days, int) and 0 <= days <= 3650:
            return reference + timedelta(days=days)
    return None


def extract_measurements(value: str) -> list[dict[str, int | float | str]]:
    """Extract numeric amount/unit pairs without converting between units."""

    aliases = sorted(
        ((alias, canonical) for canonical, values in _UNIT_ALIASES.items() for alias in values),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
    unit_pattern = "|".join(re.escape(alias) for alias, _ in aliases)
    amounts = sorted(_NUMBER_WORDS, key=len, reverse=True)
    amount_pattern = r"(?:\d+(?:\.\d+)?|" + "|".join(re.escape(word) for word in amounts) + r")"
    pattern = re.compile(
        rf"(?<![\w.])(?P<amount>{amount_pattern})\s*(?P<unit>{unit_pattern})(?![\w])",
        flags=re.IGNORECASE,
    )
    canonical_units = {alias.casefold(): canonical for alias, canonical in aliases}
    measurements: list[dict[str, int | float | str]] = []
    normalized = normalize_bengali_digits(value).casefold()
    for match in pattern.finditer(normalized):
        amount = parse_bangla_number(match.group("amount"))
        unit = canonical_units.get(match.group("unit").casefold())
        if amount is not None and unit is not None:
            measurements.append({"value": amount, "unit": unit})
    return measurements


def detect_bangla_intent(value: str) -> str | None:
    """Return a narrow M5 intent for clearly recognizable Bengali farm questions."""

    text = value.casefold()
    rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("disease_inquiry", ("রোগ", "পোকা", "কীট", "পাতায় দাগ", "পাতায় দাগ", "পাতা হলুদ", "ছত্রাক")),
        ("weather_inquiry", ("বৃষ্টি", "আবহাওয়া", "আবহাওয়া", "তাপমাত্রা", "ঝড়", "ঝড়", "পূর্বাভাস", "শিলাবৃষ্টি")),
        ("task_inquiry", ("কাজ", "কখন সেচ", "সেচ দিতে", "সার দেব", "সার দিতে", "করব", "করব কি", "করণীয়", "করনীয়")),
        ("resource_inquiry", ("মাটি", "জমির ধরন", "সেচ ব্যবস্থা", "সেচের ব্যবস্থা", "পানির উৎস", "জলের উৎস", "সরঞ্জাম", "যন্ত্রপাতি", "বাজেট")),
        ("crop_advice", ("কোন ফসল", "কোন ধান", "ধানের জাত", "কোন জাত", "ফসল লাগাব", "চাষ করব", "বীজ বপন")),
        ("onboarding_help", ("অনবোর্ডিং", "প্রোফাইল", "খামারের তথ্য", "জমির পরিমাণ")),
    )
    for intent, phrases in rules:
        if any(phrase in text for phrase in phrases):
            return intent
    return None

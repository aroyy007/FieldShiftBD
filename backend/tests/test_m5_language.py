from datetime import date

import pytest

from app.services.chat_engine import classify_intent
from app.services.m5_language import (
    extract_measurements,
    normalize_bengali_digits,
    parse_bangla_date,
    parse_bangla_number,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("০১২৩৪৫৬৭৮৯", "0123456789"), ("৩.৫", "3.5"), ("rice ১২ kg", "rice 12 kg")],
)
def test_bengali_digits_are_normalized_without_changing_other_text(value, expected):
    assert normalize_bengali_digits(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("শূন্য", 0), ("দুই", 2), ("বারো", 12), ("একশো", 100), ("১২", 12)],
)
def test_bengali_number_parser_supports_common_words_and_digits(value, expected):
    assert parse_bangla_number(value) == expected


def test_bengali_number_parser_does_not_guess_unknown_or_ambiguous_words():
    assert parse_bangla_number("কাল") is None
    assert parse_bangla_number("একটু") is None


@pytest.mark.parametrize(
    ("text", "today", "expected"),
    [
        ("আজ সেচ দিন", date(2026, 10, 29), date(2026, 10, 29)),
        ("আগামীকাল সার দিন", date(2026, 10, 29), date(2026, 10, 30)),
        ("পরশু মাঠ দেখব", date(2026, 10, 29), date(2026, 10, 31)),
        ("৩ দিন পরে", date(2026, 10, 29), date(2026, 11, 1)),
        ("০৩/১১/২০২৬", date(2026, 10, 29), date(2026, 11, 3)),
        ("2026-11-03", date(2026, 10, 29), date(2026, 11, 3)),
    ],
)
def test_bengali_dates_parse_explicit_and_relative_dates(text, today, expected):
    assert parse_bangla_date(text, today=today) == expected


def test_bare_kal_and_invalid_dates_are_not_interpreted_as_a_specific_date():
    assert parse_bangla_date("কাল") is None
    assert parse_bangla_date("৩২/১৩/২০২৬") is None


def test_measurement_parser_normalizes_bangla_amounts_and_units():
    assert extract_measurements("২.৫ কেজি বীজ, দুই লিটার পানি, ২০ মিমি বৃষ্টি") == [
        {"value": 2.5, "unit": "kg"},
        {"value": 2, "unit": "L"},
        {"value": 20, "unit": "mm"},
    ]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("ধানের পাতায় দাগ দেখা যাচ্ছে", "disease_inquiry"),
        ("আগামীকাল বৃষ্টি হবে কি", "weather_inquiry"),
        ("আজ জমিতে কী কাজ করব", "task_inquiry"),
        ("আমার মাটির ধরন কী", "resource_inquiry"),
        ("কোন ধানের জাত লাগাব", "crop_advice"),
    ],
)
def test_chat_intent_classifier_understands_common_bangla_farmer_questions(message, expected):
    assert classify_intent(message) == expected

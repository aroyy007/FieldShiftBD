"""M1 reference vocabularies: soil, land type, geography, crop aliases."""

import pytest

from app.services import m1_reference as ref


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("Loam", "loam"),
        ("loamy soil", "loam"),
        ("দো-আঁশ", "loam"),
        ("দোআঁশ মাটি", "loam"),
        ("এটেল দোআঁশ", "clay_loam"),
        ("Clay loam", "clay_loam"),
        ("বেলে দোআঁশ", "sandy_loam"),
        ("CLAY", "clay"),
        ("mud", None),
        ("", None),
        (None, None),
    ],
)
def test_soil_texture_aliases_resolve_to_canonical_codes(value, code):
    assert ref.soil_texture_code(value) == code


def test_unknown_soil_text_is_kept_but_recognized_text_is_canonical():
    assert ref.canonical_soil_label("দো-আঁশ") == "Loam"
    assert ref.canonical_soil_label("  red earth  ") == "red earth"
    assert ref.canonical_soil_label("   ") is None


@pytest.mark.parametrize(
    ("value", "code"),
    [("high", "high"), ("Medium high land", "medium_high"), ("মাঝারি উঁচু জমি", "medium_high"), ("অতি নিচু জমি", "very_low")],
)
def test_land_type_aliases(value, code):
    assert ref.canonical_land_type(value) == code


def test_unknown_land_type_is_rejected():
    with pytest.raises(ref.ReferenceDataError):
        ref.canonical_land_type("hilly")


def test_district_alias_maps_to_bbs_geocode_and_current_spelling():
    resolved = ref.resolve_location(None, "Comilla", "Adarsha Sadar")
    assert (resolved.district, resolved.district_code) == ("Cumilla", "2019")
    assert (resolved.division, resolved.division_code) == ("Chattogram", "20")
    assert resolved.upazila_code == "201967"
    assert {"BD", "BD-DIV-20", "BD-DIST-2019", "BD-UPZ-201967"} == resolved.region_codes()


def test_division_conflicting_with_district_is_rejected():
    with pytest.raises(ref.ReferenceDataError):
        ref.resolve_location("Sylhet", "Cumilla", None)


def test_unknown_upazila_is_kept_without_a_code():
    resolved = ref.resolve_location("Dhaka", "Gazipur", "Not A Real Upazila")
    assert resolved.upazila == "Not A Real Upazila"
    assert resolved.upazila_code is None
    assert "upazila_not_in_reference" in resolved.notes


def test_legacy_comilla_upazila_is_not_mapped_without_a_source():
    # The pre-split "Comilla" upazila is not one of BARC's current upazilas.
    resolved = ref.resolve_location(None, "Comilla", "Comilla")
    assert resolved.upazila_code is None


def test_geography_covers_all_districts_and_divisions():
    tree = ref.location_reference()
    assert len(tree) == 8
    assert sum(len(division["districts"]) for division in tree) == 64


@pytest.mark.parametrize(
    ("name", "key"),
    [("Corn", "maize"), ("ভুট্টা", "maize"), ("আলু", "potato"), ("Rice (Boro)", "rice"), ("Sweet Potato", None)],
)
def test_crop_aliases(name, key):
    assert ref.crop_key_for_name(name) == key

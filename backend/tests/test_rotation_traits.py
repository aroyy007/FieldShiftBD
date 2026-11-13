from datetime import date

from src.compute.rotation_traits import exploration_order, normalize_crop, season_from_date, sequence_traits


def test_normalize_crop_handles_free_text_and_bangla_transliteration():
    assert normalize_crop('Potato') == 'potato'
    assert normalize_crop('Boro paddy') == 'rice'
    assert normalize_crop('dhaincha') == 'sesbania_rostrata'
    assert normalize_crop('') is None


def test_season_from_planting_month():
    assert season_from_date(date(2026, 1, 15)) == 'boro'
    assert season_from_date(date(2026, 4, 1)) == 'aus'
    assert season_from_date(date(2026, 8, 1)) == 'aman'
    assert season_from_date(None) is None


def test_sequence_traits_counts_irrigation_families_and_legumes():
    boro_aman = sequence_traits([{'crop_code': 'rice', 'season_code': 'boro'}, {'crop_code': 'rice', 'season_code': 'aman'}])
    assert boro_aman['irrigated_dry_season_steps'] == 1 and boro_aman['family_count'] == 1 and boro_aman['legume_steps'] == 0
    chickpea = sequence_traits([{'crop_code': 'chickpea', 'season_code': 'rabi'}, {'crop_code': 'rice', 'season_code': 'aus'},
                                {'crop_code': 'rice', 'season_code': 'aman'}])
    assert chickpea['irrigated_dry_season_steps'] == 0 and chickpea['family_count'] == 2 and chickpea['legume_steps'] == 1
    unknown = sequence_traits([{'crop_code': 'rice', 'season_code': None}])
    assert unknown['unknown_water_steps'] == 1


def _options():
    return [
        {'option_id': 'two-rice', 'eligibility': 'unknown', 'metrics': {'irrigated_dry_season_steps': 1, 'crop_family_count': 1}},
        {'option_id': 'pulse', 'eligibility': 'unknown', 'metrics': {'irrigated_dry_season_steps': 0, 'crop_family_count': 2}},
        {'option_id': 'mixed', 'eligibility': 'unknown', 'metrics': {'irrigated_dry_season_steps': 1, 'crop_family_count': 2}},
        {'option_id': 'outside', 'eligibility': 'ineligible', 'metrics': {'irrigated_dry_season_steps': 0, 'crop_family_count': 3}},
    ]


def test_priority_changes_the_exploration_order():
    water = exploration_order(_options(), ['water', 'diversity'])
    assert [e['option_id'] for e in water['order']] == ['pulse', 'mixed', 'two-rice']
    diversity = exploration_order(_options(), ['diversity', 'water'])
    assert [e['option_id'] for e in diversity['order']] == ['pulse', 'mixed', 'two-rice']
    assert [e['position'] for e in diversity['order']] == [1, 2, 3]
    only_diversity = exploration_order(_options(), ['diversity'])
    assert [e['position'] for e in only_diversity['order']] == [1, 1, 3]
    assert water['unranked'] == [{'option_id': 'outside', 'reason': 'outside_documented_conditions'}]


def test_missing_first_priority_is_unranked_not_invented():
    result = exploration_order(_options(), ['income'])
    assert result['status'] == 'insufficient_evidence' and result['order'] == []
    assert {u['reason'] for u in result['unranked']} == {'missing_market_income_evidence', 'outside_documented_conditions'}


def test_short_secret_key_is_rejected():
    import pytest
    from app.core.config import Settings
    base = dict(DB_USER='a', DB_PASSWORD='b', DB_HOST='c', DB_PORT=1, DB_NAME='d', DATABASE_URL='x')
    with pytest.raises(ValueError, match='SECRET_KEY must be at least 32'):
        Settings(SECRET_KEY='', **base)
    assert Settings(SECRET_KEY='x' * 32, **base).SECRET_KEY == 'x' * 32

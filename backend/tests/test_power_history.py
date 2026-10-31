from datetime import date

from app.services.climate.power_history import parse_power_daily_response


def test_real_geojson_series_take_precedence_over_parameter_metadata_and_keep_mj_units():
    # Mirrors NASA's actual GeoJSON structure, not just a normalized fixture.
    payload = {
        "properties": {"parameter": {
            "PRECTOTCORR": {"20010101": 0.09},
            "T2M": {"20010101": 17.84},
            "ALLSKY_SFC_SW_DWN": {"20010101": 8.68},
        }},
        "parameters": {
            "PRECTOTCORR": {"units": "mm/day"},
            "T2M": {"units": "C"},
            "ALLSKY_SFC_SW_DWN": {"units": "MJ/m^2/day"},
        },
    }
    rows, coverage = parse_power_daily_response(payload, date(2001, 1, 1), date(2001, 1, 1))
    assert len(rows) == 1
    assert rows[0].solar_mj_m2_day == 8.68
    assert all(item.valid_observations == 1 for item in coverage)


def test_unknown_live_solar_units_are_rejected_instead_of_guessed():
    import pytest
    payload = {
        "properties": {"parameter": {
            "PRECTOTCORR": {"20010101": 1}, "T2M": {"20010101": 20},
            "ALLSKY_SFC_SW_DWN": {"20010101": 10},
        }},
        "parameters": {"ALLSKY_SFC_SW_DWN": {"units": "unknown"}},
    }
    with pytest.raises(ValueError, match="solar.*unit"):
        parse_power_daily_response(payload, date(2001, 1, 1), date(2001, 1, 1))


def test_parses_daily_power_values_and_preserves_missing_days_as_gaps():
    payload = {
        "parameters": {
            "PRECTOTCORR": {"20200101": 2.5, "20200102": -999.0, "20200103": 0.0},
            "T2M": {"20200101": 20.0, "20200102": 21.0, "20200103": 22.0},
            "ALLSKY_SFC_SW_DWN": {"20200101": 10.0, "20200102": 11.0, "20200103": 12.0},
        }
    }

    observations, coverage = parse_power_daily_response(
        payload, date(2020, 1, 1), date(2020, 1, 3)
    )

    assert [item.date for item in observations] == [date(2020, 1, 1), date(2020, 1, 3)]
    assert observations[0].rainfall_mm == 2.5
    assert observations[1].rainfall_mm == 0
    assert {item.variable: item.valid_observations for item in coverage} == {
        "rainfall_mm": 2,
        "temperature_c": 3,
        "solar_mj_m2_day": 3,
    }


def test_rejects_invalid_coordinates_and_date_ranges():
    import pytest

    from app.services.climate.power_history import build_power_daily_url

    assert build_power_daily_url(23.5, 90.4, date(2001, 1, 1), date(2025, 12, 31)).startswith(
        "https://power.larc.nasa.gov/api/temporal/daily/point?"
    )
    with pytest.raises(ValueError, match="latitude"):
        build_power_daily_url(91, 90.4, date(2001, 1, 1), date(2025, 12, 31))
    with pytest.raises(ValueError, match="end"):
        build_power_daily_url(23.5, 90.4, date(2025, 1, 1), date(2001, 1, 1))

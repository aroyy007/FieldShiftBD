import json
from datetime import date
from app.services.climate.power_history import NasaPowerHistoryProvider


def test_provider_fetches_and_reuses_cached_power_bundle(tmp_path, monkeypatch):
    payload = {
        "parameters": {
            "PRECTOTCORR": {"20200101": 2.5},
            "T2M": {"20200101": 20},
            "ALLSKY_SFC_SW_DWN": {"20200101": 10},
        }
    }
    calls = []

    def fake_request(url):
        calls.append(url)
        return payload

    monkeypatch.setattr("app.services.climate.power_history._request_power", fake_request)
    provider = NasaPowerHistoryProvider(tmp_path)

    first = provider.get_bundle("BD-30", 23.5, 90.4, date(2020, 1, 1), date(2020, 1, 1))
    second = provider.get_bundle(
        "BD-30", 23.5, 90.4, date(2020, 1, 1), date(2020, 1, 1), offline=True
    )

    assert len(calls) == 1
    assert second.daily_series == first.daily_series
    assert list(tmp_path.rglob("*.json"))
    assert first.daily_series[0].solar_mj_m2_day == 36

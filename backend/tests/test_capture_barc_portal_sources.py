import pytest
import httpx

from scripts.capture_barc_portal_sources import (
    Capturer,
    install_capture_tree,
    select_suitability_districts,
)


DISTRICTS = [
    {"district_c": "1004", "district_n": "Barisal"},
    {"district_c": 2019, "district_n": "Cumilla"},
]


def test_suitability_capture_defaults_to_all_available_districts():
    selected = select_suitability_districts(DISTRICTS)

    assert [str(int(item["district_c"])) for item in selected] == ["1004", "2019"]


def test_suitability_capture_can_be_limited_to_requested_districts():
    selected = select_suitability_districts(DISTRICTS, {"2019"})

    assert [str(int(item["district_c"])) for item in selected] == ["2019"]


def test_suitability_capture_rejects_unknown_district_codes():
    with pytest.raises(ValueError, match="unknown district code.*9999"):
        select_suitability_districts(DISTRICTS, {"9999"})


def test_capture_tree_replaces_old_snapshot_only_after_staging_is_ready(tmp_path):
    destination = tmp_path / "captures"
    destination.mkdir()
    (destination / "old.json").write_text("old")
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "new.json").write_text("new")

    install_capture_tree(staging, destination)

    assert not (destination / "old.json").exists()
    assert (destination / "new.json").read_text() == "new"
    assert not staging.exists()


def test_capture_tree_keeps_previous_snapshot_if_staging_is_missing(tmp_path):
    destination = tmp_path / "captures"
    destination.mkdir()
    (destination / "old.json").write_text("old")

    with pytest.raises(FileNotFoundError):
        install_capture_tree(tmp_path / "missing", destination)

    assert (destination / "old.json").read_text() == "old"


def test_capturer_retries_429_after_retry_after_header(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr("scripts.capture_barc_portal_sources.time.sleep", waits.append)
    responses = [
        httpx.Response(429, headers={"Retry-After": "3"}),
        httpx.Response(200, content=b"{}", headers={"content-type": "application/json"}),
    ]

    class Client:
        def get(self, _url):
            response = responses.pop(0)
            response.request = httpx.Request("GET", "https://example.test/data")
            return response

    capturer = Capturer(Client(), tmp_path)

    result = capturer.get("https://example.test/data", "sample.json")

    assert result == b"{}"
    assert waits[0] == 3.0
    assert 0 <= waits[1] < 0.8
    assert (tmp_path / "sample.json").read_bytes() == b"{}"


def test_capturer_caps_invalid_retry_after_with_exponential_backoff():
    response = httpx.Response(429, headers={"Retry-After": "later"})

    assert Capturer._retry_delay(response, 2) == 20.0


def test_get_many_fetches_without_overlapping_requests(tmp_path):
    class Client:
        active = 0
        maximum_active = 0

        def get(self, url):
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
            response = httpx.Response(
                200,
                content=url.encode(),
                request=httpx.Request("GET", url),
            )
            self.active -= 1
            return response

    client = Client()
    capturer = Capturer(client, tmp_path)

    bodies = capturer.get_many([
        ("https://example.test/1", "1.json"),
        ("https://example.test/2", "2.json"),
    ])

    assert bodies == [b"https://example.test/1", b"https://example.test/2"]
    assert client.maximum_active == 1

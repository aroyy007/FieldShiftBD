"""Explicit acquisition job; public advisory requests never run this job.

Supply coordinates for a publicly sourced representative point. This does not
claim a district average, centroid or village/field measurement.
"""

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from app.services.climate.district_publish import publish_district_bundle
from app.services.climate.power_history import NasaPowerHistoryProvider
from app.services.district_advisory import district_for_input


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", required=True, help="Canonical district name or 4-digit BBS code")
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--point-description", required=True)
    parser.add_argument("--point-source-url", required=True)
    parser.add_argument("--cache-root", type=Path, default=Path("data/climate/cache"))
    parser.add_argument("--offline", action="store_true", help="Use existing POWER history cache only")
    parser.add_argument("--input-json", type=Path, help="Replay a saved official NASA GeoJSON response instead of another download")
    parser.add_argument("--retrieved-at", help="Original timezone-aware acquisition timestamp; required with --input-json")
    args = parser.parse_args()
    district = district_for_input(args.district)
    # Metadata is validated before making a request, so unusable locations do
    # not create an orphan source download.
    from app.contracts.challenge.v1 import ClimateSamplingPoint
    point = ClimateSamplingPoint(
        latitude=args.latitude, longitude=args.longitude,
        description=args.point_description, source_url=args.point_source_url,
    )
    fetcher = None
    acquired_at = None
    if args.input_json:
        if args.offline or not args.retrieved_at:
            parser.error("--input-json requires --retrieved-at and cannot be combined with --offline")
        try:
            acquired_at = datetime.fromisoformat(args.retrieved_at.replace("Z", "+00:00"))
            if acquired_at.tzinfo is None or acquired_at > datetime.now(timezone.utc):
                raise ValueError("invalid acquisition timestamp")
        except ValueError:
            parser.error("--retrieved-at must be timezone-aware and not in the future")
        if args.input_json.stat().st_size > 32 * 1024 * 1024:
            parser.error("saved NASA response exceeds 32 MiB")
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
        coordinates = payload.get("geometry", {}).get("coordinates", [])
        if (len(coordinates) < 2 or abs(coordinates[0] - point.longitude) > 0.0001
                or abs(coordinates[1] - point.latitude) > 0.0001):
            parser.error("saved response coordinates do not match the requested public point")
        header = payload.get("header", {})
        if header.get("time_standard") != "UTC" or str(header.get("start")) != "20010101" or str(header.get("end")) != "20251231":
            parser.error("saved response must contain UTC daily data for 2001–2025")
        fetcher = lambda _url: payload
    elif args.retrieved_at:
        parser.error("--retrieved-at is only valid with --input-json")
    bundle = NasaPowerHistoryProvider(args.cache_root, fetcher=fetcher).get_bundle(
        district.code, point.latitude, point.longitude,
        date(2001, 1, 1), date(2025, 12, 31), offline=args.offline,
        refresh=bool(args.input_json), source_retrieved_at=acquired_at,
    )
    path = publish_district_bundle(args.cache_root, district.code, bundle, point.model_dump())
    print(f"Published {district.code}: {path}; representative point, not district mean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

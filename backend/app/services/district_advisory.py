"""Public, cache-only climate evidence; no private farm reads or writes."""

from pathlib import Path

from app.contracts.challenge.ports import ArtifactNotFound
from app.schemas.planting_window import DistrictClimateEvidence, PublicPlantingWindowEvidence
from app.services.climate.cache import ClimateBundleCache
from app.services.crop_calendar_references import published_calendar_references
from app.services.m1_reference import geography, normalize_text
from src.compute.agro import compare_annual_onsets


def district_for_input(value: str):
    key = normalize_text(value.removeprefix("BD-DIST-"))
    for district in geography().districts.values():
        if key in {normalize_text(item) for item in (district.code, district.name, district.name_bn, *district.aliases)}:
            return district
    raise ValueError("Choose a canonical Bangladesh district name or 4-digit district code")


def load_district_climate_evidence(root: Path, district_input: str) -> DistrictClimateEvidence:
    district = district_for_input(district_input)
    bundle = ClimateBundleCache(root).load_bundle(district.code)
    manifest = bundle.manifest
    if (manifest.sampling_point is None or not manifest.provenance
            or manifest.quality_status == "synthetic"
            or not any(item.method == "nasa_power" for item in manifest.provenance)
            or any(item.quality_status in {"synthetic", "unavailable", "stale"} for item in manifest.provenance)):
        raise ArtifactNotFound("district NASA cache lacks publishable point/source provenance")
    comparison = compare_annual_onsets(
        {item.date: item.rainfall_mm for item in bundle.daily_series},
        season_start_month=5, season_start_day=1, season_end_month=10, season_end_day=31,
    )
    return DistrictClimateEvidence(
        status="provisional" if comparison["status"] == "available" else "insufficient_data",
        annual_comparison=comparison,
        data_provenance={
            "source": "NASA POWER Daily Point", "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
            "dataset": "POWER Daily API, community AG; UTC days",
            "variables": ["precipitation (mm/day)", "temperature (°C)", "solar radiation (MJ/m²/day)"],
            "temporal_start": manifest.coverage_start, "temporal_end": manifest.coverage_end,
            "spatial_resolution_m": 50000,
            "spatial_scale": "Representative point grid, approximately 50 km; not a district average or field measurement",
            "cache_status": "hit", "retrieved_at": next(item.retrieved_at for item in manifest.provenance if item.method == "nasa_power"),
            "district_code": district.code,
            "sampling_point": manifest.sampling_point.model_dump(),
            "coverage_by_variable": [item.model_dump() for item in manifest.coverage_by_variable],
        },
        limitations_bn=[
            "মে–অক্টোবরের ৭ দিনের বৃষ্টি ≥২০ মিমি, পরের ১৪ দিনে একটানা ৭ দিনের বেশি শুকনো দিন নেই—এই পরীক্ষামূলক সংজ্ঞা ব্যবহার করা হয়েছে; শুকনো দিন মানে বৃষ্টি ≤১ মিমি। কৃষিবিদের পর্যালোচনা বাকি।",
            "এটি ঐতিহাসিক বৃষ্টির সংজ্ঞাভিত্তিক তুলনা; বোরোর সেচ বা অন্য ফসলের রোপণের শর্ত হিসেবে ব্যবহার করবেন না।",
        ],
        limitations_en=[
            "Exploratory definition pending review: May–October, 7-day rainfall ≥20 mm followed by 14 days without a dry run longer than 7 days; dry means ≤1 mm/day.",
            "This historical rainfall definition is not an irrigated Boro planting trigger or a crop-specific feasibility rule.",
        ],
    )


def public_advisory(root: Path, district_input: str, crop: str, season: str | None) -> PublicPlantingWindowEvidence:
    district = district_for_input(district_input)
    references = published_calendar_references(crop, season)
    season_key = season.casefold().strip() if season else None
    common = {
        "district_code": district.code, "district_name": district.name,
        "district_name_bn": district.name_bn, "season": season_key,
        "calendar_references": references,
        "sms_bn": "প্রকাশিত জাতের ক্যালেন্ডার দেখুন। স্থানীয় অবস্থা যাচাই করুন; রোপণের তারিখ বদলের সুপারিশ এখনও যাচাই হয়নি।",
        "sms_en": "Check the published variety calendar and local conditions. A climate-based planting-date adjustment is not yet validated.",
    }
    if not season:
        return PublicPlantingWindowEvidence(
            status="needs_selection", message_bn="আমন, আউশ বা বোরো মৌসুম বেছে নিন।",
            message_en="Choose Aman, Aus or Boro to view published references and climate context.", **common,
        )
    if season_key != "aman":
        # The current rainfall-onset definition is an exploratory monsoon/Aman
        # definition. Reusing it for pre-monsoon Aus or irrigated Boro would
        # imply a crop calendar rule that the sources and agronomy review do
        # not support. Keep the published variety references visible, but do
        # not fetch or display an irrelevant climate comparison.
        return PublicPlantingWindowEvidence(
            status="insufficient_data",
            message_bn=(
                "বর্তমান বৃষ্টির শুরু নির্ণয়ের পদ্ধতি শুধু আমন মৌসুমের পরীক্ষামূলক প্রেক্ষাপটে। "
                "আউশ বা বোরোর জন্য আলাদা যাচাইকৃত পদ্ধতি ও পর্যাপ্ত প্রমাণ নেই; তাই তুলনা বা রোপণের তারিখের পরামর্শ দেখানো হচ্ছে না।"
            ),
            message_en=(
                "The current rainfall-onset method is exploratory for Aman only. "
                "A separate reviewed method and adequate evidence are not available for Aus or Boro, "
                "so no comparison or planting-date advice is shown."
            ),
            limitations_bn=[
                "প্রকাশিত জাতের ক্যালেন্ডার দেখা যাচ্ছে; NASA বৃষ্টির তুলনা, GDD বা রোপণের তারিখ বদলের নিয়ম এই মৌসুমের জন্য যাচাই করা হয়নি।"
            ],
            limitations_en=[
                "Published variety calendars are shown; NASA rainfall comparison, GDD, and a planting-date adjustment rule have not been validated for this season."
            ],
            **common,
        )
    climate = load_district_climate_evidence(root, district.code)
    enough = climate.status == "provisional"
    return PublicPlantingWindowEvidence(
        status=climate.status,
        message_bn=("ঐতিহাসিক বৃষ্টির তুলনা ও প্রকাশিত জাতের ক্যালেন্ডার দেখুন। রোপণের তারিখ পরিবর্তনের আগে স্থানীয় কৃষি পরামর্শ নিন।"
                    if enough else "ক্যাশে পর্যাপ্ত সম্পূর্ণ বছরের বৃষ্টি নেই। প্রকাশিত জাতের ক্যালেন্ডার দেখুন এবং স্থানীয় কৃষি পরামর্শ নিন।"),
        message_en=("Explore historical rainfall timing and published variety calendars. Check local agricultural advice before changing planting dates."
                    if enough else "The cache lacks enough complete rainfall years. Check the published calendar and local agricultural advice."),
        annual_comparison=climate.annual_comparison,
        data_provenance=climate.data_provenance,
        limitations_bn=climate.limitations_bn + ["জাতভিত্তিক GDD পদ্ধতি ও রোপণের সময় বদলানোর নিয়ম যাচাই বাকি। GDD বা তারিখ বদলের সংখ্যা তৈরি করা হয়নি।"],
        limitations_en=climate.limitations_en + ["Cultivar GDD inputs and planting-shift policy await review; GDD and recommended shifts remain unavailable."],
        **common,
    )

import json
from importlib import import_module
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app
from app.schemas.chat import ChatResponse
from app.schemas.disease import DiseaseProblemSyncResponse
from app.schemas.farm_state import FarmStateRead, PlanTaskImportRequest
from app.schemas.m2_advisor import CropRecommendationSet, FarmProfileInput
from app.schemas.weather import WeatherAssessmentOut

MANIFEST = Path(__file__).parents[1] / "contracts" / "module-ownership.json"
FIXTURES = Path(__file__).parent / "fixtures" / "modules"


def test_all_six_modules_declare_owned_routes_and_models():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    foundation = manifest["shared_foundation"]
    assert foundation["contract_version"] == "1.0.0"
    assert foundation["feature_flags_default"] is False
    assert foundation["alembic_revision"] == "c6f4e739a2b1"
    assert "get" in app.openapi()["paths"][foundation["availability_endpoint"]]
    assert set(manifest["modules"]) == {f"M{i}" for i in range(1, 7)}
    openapi = app.openapi()
    seen_operations = set()
    for module_id, module in manifest["modules"].items():
        assert module["router_imports"]
        assert module["owned_models"]
        assert module["interfaces"]
        router_routes = set()
        for reference in module["router_imports"]:
            module_path, attribute_path = reference.split(":", maxsplit=1)
            router = import_module(module_path)
            for attribute in attribute_path.split("."):
                router = getattr(router, attribute)
            router_routes.update(
                (method.lower(), route.path)
                for route in router.routes
                if isinstance(route, APIRoute)
                for method in route.methods or ()
            )
        for interface in module["interfaces"]:
            operation = (interface["method"].lower(), interface["path"])
            assert operation not in seen_operations, (
                f"{operation} has multiple owners"
            )
            seen_operations.add(operation)
            assert operation in router_routes, f"{module_id} does not own {operation}"
            assert operation[1] in openapi["paths"], (
                f"{module_id} route missing: {operation}"
            )
            assert operation[0] in openapi["paths"][operation[1]], (
                f"{module_id} method missing: {operation}"
            )
        declared_routes = {
            (interface["method"].lower(), interface["path"])
            for interface in module["interfaces"]
        }
        assert router_routes == declared_routes, (
            f"{module_id} route inventory is stale; "
            f"unlisted={router_routes - declared_routes}, "
            f"unregistered={declared_routes - router_routes}"
        )
        for model in module["owned_models"]:
            module_path, class_name = model.rsplit(".", 1)
            imported = __import__(module_path, fromlist=[class_name])
            assert hasattr(imported, class_name), f"{module_id} model missing: {model}"


def test_module_seam_request_and_response_schemas_are_stable():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    openapi = app.openapi()
    schemas = openapi["components"]["schemas"]

    for module_id, module in manifest["modules"].items():
        for contract in module.get("contract_checks", []):
            operation = openapi["paths"][contract["path"]][contract["method"]]
            if "request_schema" in contract:
                request_schema = operation["requestBody"]["content"][
                    "application/json"
                ]["schema"]
                assert request_schema["$ref"].endswith(
                    f"/{contract['request_schema']}"
                ), f"{module_id} request schema changed for {contract['path']}"
                request_model = schemas[contract["request_schema"]]
                assert set(contract["request_required"]) == set(
                    request_model.get("required", ())
                ), f"{module_id} request required fields changed for {contract['path']}"
                assert set(contract.get("request_properties", ())) <= set(
                    request_model.get("properties", ())
                )

            response = operation["responses"][contract["success_status"]]
            response_schema = response["content"]["application/json"]["schema"]
            assert response_schema["$ref"].endswith(
                f"/{contract['response_schema']}"
            ), f"{module_id} response schema changed for {contract['path']}"
            response_model = schemas[contract["response_schema"]]
            assert set(contract["response_required"]) == set(
                response_model.get("required", ())
            ), f"{module_id} response required fields changed for {contract['path']}"
            for field, allowed_values in contract.get("enum_values", {}).items():
                model_name, property_name = field.split(".", maxsplit=1)
                assert schemas[model_name]["properties"][property_name]["enum"] == (
                    allowed_values
                ), f"{module_id} enum changed for {field}"


def test_each_module_can_use_schema_validated_seam_mocks():
    mocks_path = FIXTURES / "integration-mocks.json"
    mocks = json.loads(mocks_path.read_text(encoding="utf-8"))
    assert "SYNTHETIC CONTRACT MOCKS ONLY" in mocks.pop("test_only_warning")

    golden_farm = json.loads(
        (
            Path(__file__).parent
            / "fixtures"
            / "m2"
            / "synthetic_golden_farm.json"
        ).read_text(encoding="utf-8")
    )
    FarmProfileInput.model_validate(golden_farm["farm_profile"])
    CropRecommendationSet.model_validate(mocks["m2_recommendation_set"])
    PlanTaskImportRequest.model_validate(mocks["m2_plan_tasks_to_m3"])
    FarmStateRead.model_validate(mocks["m3_farm_state_to_consumers"])
    WeatherAssessmentOut.model_validate(mocks["m4_weather_assessment_to_consumers"])
    ChatResponse.model_validate(mocks["m5_chat_response_to_frontend"])
    DiseaseProblemSyncResponse.model_validate(
        mocks["m6_disease_sync_to_m3_and_frontend"]
    )

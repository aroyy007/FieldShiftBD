from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import httpx

import pytest
from PIL import Image

from app.api.routes_disease import (
    get_disease_predictor,
    get_gemini_verifier,
    get_module3_gateway,
)
from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.main import app
from app.models.foundation import ConsentRecord
from app.schemas.farm_state import FarmStateRead, ProblemCreate, ProblemRead
from app.services.disease_inference import DiseasePrediction
from app.services.gemini_verification import (
    GeminiApiVerifier,
    GeminiAssessment,
    GeminiVerificationError,
)
from app.services.module3_client import Module3ApiClient, Module3ClientError


class FakePredictor:
    def __init__(self, label: str, score: float):
        self.label = label
        self.score = score
        self.calls = 0

    def predict(self, image):
        self.calls += 1
        assert image.mode == "RGB"
        return DiseasePrediction(label=self.label, score=self.score)


class FakeGeminiVerifier:
    def __init__(self, assessment=None, error=None):
        self.assessment = assessment
        self.error = error
        self.calls = []

    def verify(self, image, current_crop):
        self.calls.append((image.mode, current_crop))
        if self.error is not None:
            raise self.error
        return self.assessment


class FakeModule3Gateway:
    def __init__(self, state: FarmStateRead):
        self.state = state
        self.problems: list[ProblemRead] = []
        self.create_calls = 0
        self.fail_create = False

    def read_farm_state(self, farmland_id):
        if farmland_id != self.state.farmland_id:
            raise Module3ClientError(404, "Farmland not found")
        return self.state.model_copy(update={"open_problems": list(self.problems)})

    def create_problem(self, farmland_id, payload: ProblemCreate):
        self.create_calls += 1
        if self.fail_create:
            raise Module3ClientError(503, "Module 3 is temporarily unavailable")
        problem = ProblemRead(
            id=uuid4(),
            farmland_id=farmland_id,
            season_id=payload.season_id,
            source=payload.source,
            category=payload.category,
            description=payload.description,
            severity=payload.severity,
            status="open",
            created_at=datetime.now(timezone.utc),
            resolved_at=None,
        )
        self.problems.insert(0, problem)
        return problem


def png_upload() -> tuple[str, bytes, str]:
    output = BytesIO()
    Image.new("RGB", (256, 256), (40, 120, 40)).save(output, format="PNG")
    return ("leaf.png", output.getvalue(), "image/png")


def install_test_adapters(client, farmland_id, predictor, gemini_verifier=None):
    state_response = client.get("/farmlands/" + str(farmland_id) + "/state")
    assert state_response.status_code == 200
    gateway = FakeModule3Gateway(FarmStateRead.model_validate(state_response.json()))
    app.dependency_overrides[get_module3_gateway] = lambda: gateway
    app.dependency_overrides[get_disease_predictor] = lambda: predictor
    app.dependency_overrides[get_gemini_verifier] = lambda: gemini_verifier
    return gateway


def add_disease_problem_consent(client):
    farmer_id = app.dependency_overrides[get_current_farmer_id]()
    db = next(app.dependency_overrides[get_db]())
    consent = ConsentRecord(
        farmer_id=farmer_id,
        purpose="disease_problem_sync",
        version=1,
        decision="granted",
        policy_version="disease-problem-sync-2026-11-v1",
        channel="explicit_tap",
        idempotency_key="disease-consent-test-" + uuid4().hex,
        request_fingerprint="a" * 64,
        captured_at=datetime.now(timezone.utc),
    )
    db.add(consent)
    db.commit()
    return consent.id



def test_module3_http_adapter_reads_state_and_posts_problem_contract(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    state_payload = client.get("/farmlands/" + str(farmland_id) + "/state").json()
    now = datetime.now(timezone.utc).isoformat()
    requests = []

    def handler(request):
        requests.append(request)
        assert request.headers["authorization"] == "Bearer forwarded-token"
        if request.url.path.endswith("/state"):
            return httpx.Response(200, json=state_payload)

        assert request.url.path == "/farmlands/" + str(farmland_id) + "/problems"
        import json

        payload = json.loads(request.content)
        assert payload["source"] == "disease_detection"
        assert payload["category"] == "rice_blast"
        assert payload["season_id"] == str(season_id)
        return httpx.Response(
            201,
            json={
                "id": str(uuid4()),
                "farmland_id": str(farmland_id),
                "season_id": str(season_id),
                "source": "disease_detection",
                "category": "rice_blast",
                "description": "Possible rice blast.",
                "severity": "moderate",
                "status": "open",
                "created_at": now,
                "resolved_at": None,
            },
        )

    gateway = Module3ApiClient(
        "http://module3.test",
        headers={"authorization": "Bearer forwarded-token"},
        transport=httpx.MockTransport(handler),
    )
    try:
        farm_state = gateway.read_farm_state(farmland_id)
        problem = gateway.create_problem(
            farmland_id,
            ProblemCreate(
                season_id=season_id,
                source="disease_detection",
                category="rice_blast",
                description="Possible rice blast.",
            ),
        )
    finally:
        gateway.close()

    assert farm_state.active_season.crop_name == "Rice"
    assert problem.source == "disease_detection"
    assert problem.status == "open"
    assert len(requests) == 2


def test_disease_result_waits_for_farmer_confirmation_before_module3_problem(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    predictor = FakePredictor("Rice_Blast", 0.91)
    gateway = install_test_adapters(client, farmland_id, predictor)
    url = "/farmlands/" + str(farmland_id) + "/disease-results"

    first = client.post(url, files={"image": png_upload()})
    second = client.post(url, files={"image": png_upload()})

    assert first.status_code == 201
    assert first.json()["outcome"] == "possible_disease"
    assert first.json()["problem_sync"] == "awaiting_confirmation"
    assert first.json()["farm_problem"] is None
    assert first.json()["disease_result"]["model_details"]["problem_sync"] == "awaiting_confirmation"

    assert second.status_code == 201
    assert second.json()["problem_sync"] == "awaiting_confirmation"
    assert second.json()["farm_problem"] is None
    assert gateway.create_calls == 0
    assert predictor.calls == 2

    history = client.get(url)
    assert history.status_code == 200
    assert len(history.json()) == 2

    result_id = first.json()["disease_result"]["id"]
    consent_id = str(add_disease_problem_consent(client))
    sync_url = f"/farmlands/{farmland_id}/disease-results/{result_id}/sync-problem"
    confirmed = client.post(
        sync_url,
        json={
            "contract_version": "1.0.0",
            "disease_result_id": result_id,
            "farmland_id": str(farmland_id),
            "idempotency_key": f"disease-sync:{result_id}",
            "mode": "deferred_confirmation",
            "assessment": "possible_issue",
            "possible_issue": first.json()["disease_result"]["possible_issue"],
            "confidence": 0.91,
            "farmer_confirmation": "confirmed",
            "consent_receipt_id": consent_id,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["problem_sync"] == "created"
    assert confirmed.json()["farm_problem"]["source"] == "disease_detection"
    assert confirmed.json()["farm_problem"]["category"] == "rice_blast"
    assert confirmed.json()["farm_problem"]["season_id"] == first.json()["disease_result"]["season_id"]
    assert str(result_id) in confirmed.json()["farm_problem"]["description"]
    assert confirmed.json()["disease_result"]["model_details"]["problem_sync_consent_id"] == consent_id
    assert gateway.create_calls == 1
    repeated = client.post(sync_url, json={
        "contract_version": "1.0.0", "disease_result_id": result_id,
        "farmland_id": str(farmland_id), "idempotency_key": f"disease-sync:{result_id}",
        "mode": "deferred_confirmation", "assessment": "possible_issue",
        "possible_issue": first.json()["disease_result"]["possible_issue"], "confidence": 0.91,
        "farmer_confirmation": "confirmed", "consent_receipt_id": consent_id,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    })
    assert repeated.status_code == 200
    assert repeated.json()["farm_problem"]["id"] == confirmed.json()["farm_problem"]["id"]
    assert gateway.create_calls == 1


def test_disease_problem_sync_requires_confirmation_and_active_consent(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    gateway = install_test_adapters(client, farmland_id, FakePredictor("Rice_Blast", 0.91))
    scan = client.post(
        f"/farmlands/{farmland_id}/disease-results", files={"image": png_upload()}
    ).json()
    result_id = scan["disease_result"]["id"]
    url = f"/farmlands/{farmland_id}/disease-results/{result_id}/sync-problem"
    payload = {
        "contract_version": "1.0.0",
        "disease_result_id": result_id,
        "farmland_id": str(farmland_id),
        "idempotency_key": f"disease-sync:{result_id}",
        "mode": "deferred_confirmation",
        "assessment": "possible_issue",
        "possible_issue": scan["disease_result"]["possible_issue"],
        "confidence": 0.91,
        "farmer_confirmation": "confirmed",
        "consent_receipt_id": str(uuid4()),
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(url, json=payload)

    assert response.status_code == 403
    assert gateway.create_calls == 0


def test_farmer_can_decline_problem_sync_without_creating_a_problem(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    gateway = install_test_adapters(client, farmland_id, FakePredictor("Rice_Blast", 0.91))
    scan = client.post(
        f"/farmlands/{farmland_id}/disease-results", files={"image": png_upload()}
    ).json()
    saved = scan["disease_result"]

    response = client.post(
        f"/farmlands/{farmland_id}/disease-results/{saved['id']}/sync-problem",
        json={
            "contract_version": "1.0.0", "disease_result_id": saved["id"],
            "farmland_id": str(farmland_id), "idempotency_key": f"disease-sync:{saved['id']}",
            "mode": "deferred_confirmation", "assessment": "possible_issue",
            "possible_issue": saved["possible_issue"], "confidence": saved["confidence"],
            "farmer_confirmation": "denied", "requested_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json()["problem_sync"] == "declined"
    assert response.json()["farm_problem"] is None
    assert gateway.create_calls == 0


def test_failed_module3_write_can_be_retried_without_reanalysis(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    gateway = install_test_adapters(
        client,
        farmland_id,
        FakePredictor("Rice_Blast", 0.91),
    )
    result_response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )
    assert result_response.status_code == 201
    saved_result = result_response.json()["disease_result"]
    assert result_response.json()["problem_sync"] == "awaiting_confirmation"

    retry_url = (
        "/farmlands/" + str(farmland_id) + "/disease-results/"
        + saved_result["id"] + "/sync-problem"
    )
    consent_id = str(add_disease_problem_consent(client))
    payload = {
        "contract_version": "1.0.0", "disease_result_id": saved_result["id"],
        "farmland_id": str(farmland_id), "idempotency_key": f"disease-sync:{saved_result['id']}",
        "mode": "deferred_confirmation", "assessment": "possible_issue",
        "possible_issue": saved_result["possible_issue"], "confidence": 0.91, "farmer_confirmation": "confirmed",
        "consent_receipt_id": consent_id,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
    gateway.fail_create = True
    failed = client.post(retry_url, json=payload)
    assert failed.status_code == 200
    assert failed.json()["problem_sync"] == "failed"
    assert failed.json()["disease_result"]["model_details"]["problem_sync_consent_id"] == consent_id
    gateway.fail_create = False
    retried = client.post(retry_url, json=payload)
    retried_again = client.post(retry_url, json=payload)

    assert retried.status_code == 200
    assert retried.json()["problem_sync"] == "created"
    assert retried.json()["farm_problem"]["status"] == "open"
    assert retried.json()["disease_result"]["model_details"]["problem_sync"] == "created"
    assert retried_again.status_code == 200
    assert retried_again.json()["farm_problem"]["id"] == retried.json()["farm_problem"]["id"]
    assert gateway.create_calls == 2
    assert len(client.get("/farmlands/" + str(farmland_id) + "/disease-results").json()) == 1


@pytest.mark.parametrize(
    ("label", "score", "expected_outcome"),
    [
        ("Rice_normal", 0.94, "healthy"),
        ("Rice_Blast", 0.42, "uncertain"),
        ("Tomato_Early_Blight", 0.98, "uncertain"),
    ],
)
def test_healthy_uncertain_and_crop_mismatch_do_not_create_problem(
    client_and_farm, label, score, expected_outcome
):
    client, farmland_id, _, _ = client_and_farm
    predictor = FakePredictor(label, score)
    gateway = install_test_adapters(client, farmland_id, predictor)

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == expected_outcome
    if expected_outcome == "uncertain":
        assert response.json()["disease_result"]["possible_issue"] is None
    assert response.json()["problem_sync"] == "not_required"
    assert response.json()["farm_problem"] is None
    assert gateway.create_calls == 0
    assert len(client.get("/farmlands/" + str(farmland_id) + "/disease-results").json()) == 1


def test_invalid_and_oversized_images_are_rejected(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    install_test_adapters(client, farmland_id, FakePredictor("Rice_Blast", 0.9))
    url = "/farmlands/" + str(farmland_id) + "/disease-results"

    invalid = client.post(url, files={"image": ("bad.jpg", b"not an image", "image/jpeg")})
    oversized = client.post(
        url,
        files={"image": ("large.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")},
    )

    assert invalid.status_code == 400
    assert oversized.status_code == 413


def test_missing_active_season_is_rejected_before_inference(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    state = FarmStateRead.model_validate(
        client.get("/farmlands/" + str(farmland_id) + "/state").json()
    ).model_copy(update={"active_season": None})
    gateway = FakeModule3Gateway(state)
    predictor = FakePredictor("Rice_Blast", 0.9)
    app.dependency_overrides[get_module3_gateway] = lambda: gateway
    app.dependency_overrides[get_disease_predictor] = lambda: predictor

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    assert response.status_code == 409
    assert predictor.calls == 0


def test_disease_detection_requires_verified_farmer(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    authentication = app.dependency_overrides.pop(get_current_farmer_id)

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    app.dependency_overrides[get_current_farmer_id] = authentication
    assert response.status_code == 401


def test_gemini_and_local_agreement_records_possible_issue(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    verifier = FakeGeminiVerifier(
        GeminiAssessment(
            finding="possible_issue",
            crop_match="matches_current_crop",
            visible_signs="Irregular brown lesions are visible.",
        )
    )
    gateway = install_test_adapters(
        client,
        farmland_id,
        FakePredictor("Rice_Blast", 0.91),
        verifier,
    )

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "possible_disease"
    assert response.json()["verification"]["status"] == "verified_issue"
    assert response.json()["verification"]["visible_signs"] == "Irregular brown lesions are visible."
    assert response.json()["problem_sync"] == "awaiting_confirmation"
    assert response.json()["farm_problem"] is None
    assert gateway.create_calls == 0
    assert verifier.calls == [("RGB", "Rice")]


def test_gemini_disagreement_saves_uncertain_without_problem(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    verifier = FakeGeminiVerifier(
        GeminiAssessment(
            finding="healthy",
            crop_match="matches_current_crop",
            visible_signs="No clear damage is visible.",
        )
    )
    gateway = install_test_adapters(
        client,
        farmland_id,
        FakePredictor("Rice_Blast", 0.91),
        verifier,
    )

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "uncertain"
    assert response.json()["disease_result"]["possible_issue"] is None
    assert response.json()["verification"]["status"] == "disagreement"
    assert response.json()["problem_sync"] == "not_required"
    assert response.json()["farm_problem"] is None
    assert gateway.create_calls == 0


def test_gemini_only_issue_is_uncertain_and_does_not_create_problem(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    verifier = FakeGeminiVerifier(
        GeminiAssessment(
            finding="possible_issue",
            crop_match="matches_current_crop",
            visible_signs="Some discoloration is visible.",
        )
    )
    gateway = install_test_adapters(
        client,
        farmland_id,
        FakePredictor("Rice_Blast", 0.42),
        verifier,
    )

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "uncertain"
    assert response.json()["verification"]["status"] == "gemini_only_issue"
    assert response.json()["problem_sync"] == "not_required"
    assert gateway.create_calls == 0


def test_gemini_unavailable_fails_closed(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    verifier = FakeGeminiVerifier(error=GeminiVerificationError("offline"))
    gateway = install_test_adapters(
        client,
        farmland_id,
        FakePredictor("Rice_Blast", 0.91),
        verifier,
    )

    response = client.post(
        "/farmlands/" + str(farmland_id) + "/disease-results",
        files={"image": png_upload()},
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "uncertain"
    assert response.json()["verification"]["status"] == "unavailable"
    assert response.json()["problem_sync"] == "not_required"
    assert response.json()["farm_problem"] is None
    assert gateway.create_calls == 0


def test_gemini_adapter_sends_image_and_parses_structured_response():
    import base64
    import json

    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.path == "/v1/interactions"
        assert request.headers["x-goog-api-key"] == "test-only-key"
        payload = json.loads(request.content)
        assert payload["model"] == "gemini-test-model"
        assert payload["store"] is False
        assert payload["input"][1]["mime_type"] == "image/jpeg"
        image_bytes = base64.b64decode(payload["input"][1]["data"])
        with Image.open(BytesIO(image_bytes)) as decoded:
            assert decoded.size == (256, 256)
        assert '"Rice"' in payload["input"][0]["text"]
        return httpx.Response(
            200,
            json={
                "output_text": json.dumps(
                    {
                        "finding": "possible_issue",
                        "crop_match": "matches_current_crop",
                        "visible_signs": "Brown spots are visible.",
                    }
                )
            },
        )

    verifier = GeminiApiVerifier(
        "test-only-key",
        model="gemini-test-model",
        transport=httpx.MockTransport(handler),
    )
    try:
        assessment = verifier.verify(Image.new("RGB", (256, 256), (40, 120, 40)), "Rice")
    finally:
        verifier.close()

    assert assessment == GeminiAssessment(
        finding="possible_issue",
        crop_match="matches_current_crop",
        visible_signs="Brown spots are visible.",
    )
    assert len(requests) == 1

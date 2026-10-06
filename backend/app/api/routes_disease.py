import hashlib
import io
import logging
import math
import re
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import BigInteger, cast, func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.config import settings
from app.core.database import get_db
from app.models.core import Crop
from app.models.disease import DiseaseResult
from app.schemas.disease import (
    DiseaseAnalysisResponse,
    DiseaseProblemSyncResponse,
    DiseaseResultRead,
    DiseaseVerificationRead,
)
from app.schemas.farm_state import FarmStateRead, ProblemCreate, ProblemRead
from app.services.disease_inference import (
    DiseasePrediction,
    DiseasePredictor,
    InferenceUnavailableError,
    get_disease_predictor,
)
from app.services.gemini_verification import (
    GeminiVerificationError,
    GeminiVerifier,
    get_gemini_verifier,
)
from app.services.module3_client import (
    Module3ClientError,
    Module3Gateway,
    get_module3_gateway,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/farmlands", tags=["Disease detection — Module 6"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentFarmerId = Annotated[UUID, Depends(get_current_farmer_id)]
M3Gateway = Annotated[Module3Gateway, Depends(get_module3_gateway)]
Predictor = Annotated[DiseasePredictor, Depends(get_disease_predictor)]
GeminiVerifierDep = Annotated[GeminiVerifier | None, Depends(get_gemini_verifier)]

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MIN_IMAGE_EDGE = 128
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
DISCLAIMER = (
    "This is an AI screening result, not a confirmed diagnosis. Check the crop in the field "
    "and consult a local agricultural extension worker before applying treatment."
)


def _decode_image(image: UploadFile) -> Image.Image:
    content_type = (image.content_type or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP crop photo.")

    data = image.file.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Crop photos must be 10 MB or smaller.")

    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Use a JPEG, PNG, or WebP photo. Convert HEIC photos before uploading.",
                )
            width, height = source.size
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="The image dimensions are too large.")
            if min(width, height) < MIN_IMAGE_EDGE:
                raise HTTPException(
                    status_code=422,
                    detail="This photo is too small to inspect. Take a closer, higher-resolution photo.",
                )
            source.load()
            return ImageOps.exif_transpose(source).convert("RGB")
    except HTTPException:
        raise
    except Image.DecompressionBombError as error:
        raise HTTPException(status_code=413, detail="The image dimensions are too large.") from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail="The file is not a readable JPEG, PNG, or WebP image.",
        ) from error


def _normalize_crop(crop_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", crop_name.lower())
    aliases = {
        "maize": "corn",
        "corn": "corn",
        "potatoes": "potato",
    }
    return aliases.get(normalized, normalized)


def _crop_from_label(label: str) -> str:
    return label.split("_", maxsplit=1)[0]


def _is_healthy_label(label: str) -> bool:
    tokens = re.findall(r"[a-z]+", label.lower())
    return "healthy" in tokens or "normal" in tokens


def _humanize_label(label: str) -> str:
    return re.sub(r"[_\s]+", " ", label).strip().capitalize()


def _category_for_label(label: str) -> str:
    category = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return category[:80].rstrip("_") or "crop_disease"


def _confidence_level(score: float) -> Literal["low", "moderate", "high"]:
    if score >= 0.85:
        return "high"
    if score >= settings.DISEASE_CONFIDENCE_THRESHOLD:
        return "moderate"
    return "low"


def _result_read(result: DiseaseResult, crop_name: str | None) -> DiseaseResultRead:
    return DiseaseResultRead.model_validate(result).model_copy(
        update={"crop_name": crop_name}
    )


def _get_state(gateway: Module3Gateway, farmland_id: UUID) -> FarmStateRead:
    try:
        return gateway.read_farm_state(farmland_id)
    except Module3ClientError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _lock_farmland_problem_sync(db: Session, farmland_id: UUID) -> None:
    """Serialize Module 6 problem syncs for this farm across API workers."""
    if db.get_bind().dialect.name != "postgresql":
        return

    key_material = b"fieldshift-module6-problem-sync:" + farmland_id.bytes
    lock_id = int.from_bytes(
        hashlib.blake2b(key_material, digest_size=8).digest(),
        byteorder="big",
        signed=True,
    )
    db.execute(select(func.pg_advisory_xact_lock(cast(lock_id, BigInteger))))


def _sync_open_problem(
    gateway: Module3Gateway,
    farmland_id: UUID,
    season_id: UUID,
    category: str,
    description: str,
    open_problems: list[ProblemRead],
) -> tuple[ProblemRead, Literal["created", "reused"]]:
    existing_problem = next(
        (
            candidate
            for candidate in open_problems
            if candidate.season_id == season_id
            and candidate.category == category
            and candidate.source == "disease_detection"
            and candidate.status in {"open", "monitoring"}
        ),
        None,
    )
    if existing_problem is not None:
        return existing_problem, "reused"

    problem = gateway.create_problem(
        farmland_id,
        ProblemCreate(
            season_id=season_id,
            source="disease_detection",
            category=category,
            description=description,
            severity="moderate",
        ),
    )
    return problem, "created"


def _message_for_outcome(
    outcome: str,
    issue: str,
    current_crop: str,
    predicted_crop: str,
    score: float,
) -> tuple[str, list[str]]:
    if outcome == "healthy":
        return (
            "The model matched a healthy class for " + current_crop
            + ". Keep monitoring; one photo cannot rule out every crop problem.",
            ["Continue regular field checks and photograph any new symptoms."],
        )
    if score < settings.DISEASE_CONFIDENCE_THRESHOLD:
        return (
            "The photo did not produce a reliable match. Retake a clear close-up in daylight "
            "and ask a local agriculture worker if symptoms remain.",
            [
                "Photograph one affected leaf in daylight and keep the whole affected area in frame.",
                "Avoid applying treatment based only on this uncertain result.",
            ],
        )
    if _normalize_crop(predicted_crop) != _normalize_crop(current_crop):
        return (
            "The model's top class belongs to " + predicted_crop
            + ", while this farm's active season is set to " + current_crop
            + ". Confirm the crop or take another photo before using this result.",
            [
                "Confirm the active crop in the farm profile.",
                "Retake a clear photo of the crop currently growing in this field.",
            ],
        )
    return (
        "The model detected possible " + issue + " on " + current_crop
        + ". This is a screening result and needs field confirmation.",
        [
            "Inspect several nearby plants and note whether the same signs are spreading.",
            "Ask a local agricultural extension worker to confirm the issue before applying treatment.",
        ],
    )


@router.post(
    "/{farmland_id}/disease-results",
    response_model=DiseaseAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_disease(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
    gateway: M3Gateway,
    predictor: Predictor,
    gemini_verifier: GeminiVerifierDep,
    image: UploadFile = File(...),
) -> DiseaseAnalysisResponse:
    # The identity dependency enforces Module 1's verified-farmer boundary.
    _ = farmer_id
    farm_state = _get_state(gateway, farmland_id)
    active_season = farm_state.active_season
    if active_season is None:
        raise HTTPException(
            status_code=409,
            detail="An active crop season is required before checking crop disease.",
        )

    current_crop = active_season.crop_name.strip()
    if not current_crop:
        raise HTTPException(status_code=409, detail="The active season has no crop name.")

    image_data = _decode_image(image)
    try:
        prediction: DiseasePrediction = predictor.predict(image_data)
    except InferenceUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    score = float(prediction.score)
    if not math.isfinite(score) or score < 0 or score > 1 or not prediction.label:
        raise HTTPException(status_code=503, detail="The disease model returned an invalid prediction.")

    predicted_crop = _crop_from_label(prediction.label)
    if not predicted_crop:
        raise HTTPException(status_code=503, detail="The disease model returned an invalid class label.")

    threshold = settings.DISEASE_CONFIDENCE_THRESHOLD
    crop_matches = _normalize_crop(predicted_crop) == _normalize_crop(current_crop)
    if score < threshold:
        outcome = "uncertain"
    elif not crop_matches:
        outcome = "uncertain"
    elif _is_healthy_label(prediction.label):
        outcome = "healthy"
    else:
        outcome = "possible_disease"

    issue = _humanize_label(prediction.label)
    verification = DiseaseVerificationRead(status="not_configured")
    verification_message = None
    verification_actions = None

    if gemini_verifier is not None:
        try:
            assessment = gemini_verifier.verify(image_data, current_crop)
        except GeminiVerificationError:
            verification = DiseaseVerificationRead(
                status="unavailable",
                model=settings.GEMINI_MODEL,
            )
            outcome = "uncertain"
            verification_message = (
                "Gemini could not verify this photo. No farm problem was created; "
                "try again later or ask a local agricultural worker to inspect the crop."
            )
            verification_actions = [
                "Retake a clear close-up in daylight if the symptoms are still visible.",
                "Do not apply treatment based only on this unverified result.",
            ]
        else:
            verification = DiseaseVerificationRead(
                status="uncertain",
                finding=assessment.finding,
                crop_match=assessment.crop_match,
                visible_signs=assessment.visible_signs,
                model=settings.GEMINI_MODEL,
            )
            if (
                assessment.crop_match != "matches_current_crop"
                or assessment.finding in {"uncertain", "not_crop"}
            ):
                outcome = "uncertain"
                verification_message = (
                    "The image models could not confirm a problem on the active crop. "
                    "No farm problem was created. Retake a clearer photo or ask a local "
                    "agricultural worker to inspect the crop."
                )
            elif outcome == "healthy" and assessment.finding == "healthy":
                verification.status = "verified_healthy"
            elif outcome == "possible_disease" and assessment.finding == "possible_issue":
                verification.status = "verified_issue"
            elif outcome == "uncertain" and assessment.finding == "possible_issue":
                verification.status = "gemini_only_issue"
                verification_message = (
                    "Gemini saw possible crop symptoms, but the local classifier did not "
                    "confirm them. This remains uncertain, and no farm problem was created."
                )
            else:
                outcome = "uncertain"
                verification.status = "disagreement"
                verification_message = (
                    "The image models disagreed about this photo. Treat the result as "
                    "uncertain; no farm problem was created. Ask a local agricultural "
                    "worker to inspect the crop before taking action."
                )

    message, recommended_actions = _message_for_outcome(
        outcome,
        issue,
        current_crop,
        predicted_crop,
        score,
    )
    if verification_message is not None:
        message = verification_message
        verification_actions = verification_actions or [
            "Retake one clear photo of the affected area in daylight.",
            "Avoid applying treatment until the symptoms are confirmed.",
        ]
        recommended_actions = verification_actions
    growth_stage = farm_state.current_growth_stage
    result = DiseaseResult(
        farmland_id=farmland_id,
        season_id=active_season.id,
        crop_id=active_season.crop_id,
        image_storage_key=None,
        possible_issue=issue if outcome == "possible_disease" else None,
        confidence=Decimal(str(round(score, 5))),
        symptoms=[],
        recommended_actions=recommended_actions,
        model_details={
            "model_id": "Saon110/bd-crop-vegetable-plant-disease-model",
            "prediction_label": prediction.label,
            "predicted_crop": predicted_crop,
            "outcome": outcome,
            "confidence_threshold": threshold,
            "crop_matches_active_season": crop_matches,
            "gemini_verification": verification.model_dump(mode="json"),
            "growth_stage_id": str(growth_stage.id) if growth_stage else None,
            "growth_stage_name": growth_stage.name if growth_stage else None,
            "visual_symptoms_available": False,
        },
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    problem: ProblemRead | None = None
    problem_sync: Literal["not_required", "created", "reused", "failed"] = "not_required"

    if outcome == "possible_disease":
        category = _category_for_label(prediction.label)
        description = (
            "DiseaseResult " + str(result.id) + ": possible " + issue
            + "; model score " + format(score, ".2f") + "."
        )
        if growth_stage is not None:
            description += " Growth stage: " + growth_stage.name + "."
        try:
            _lock_farmland_problem_sync(db, farmland_id)
            sync_state = _get_state(gateway, farmland_id)
            problem, problem_sync = _sync_open_problem(
                gateway,
                farmland_id,
                active_season.id,
                category,
                description,
                sync_state.open_problems,
            )
        except Module3ClientError:
            logger.exception(
                "Module 3 problem write failed for disease result %s",
                result.id,
            )
            problem_sync = "failed"

        model_details = dict(result.model_details)
        model_details["problem_sync"] = problem_sync
        if problem is not None:
            model_details["farm_problem_id"] = str(problem.id)
        result.model_details = model_details
        db.commit()
        db.refresh(result)

    return DiseaseAnalysisResponse(
        disease_result=_result_read(result, current_crop),
        outcome=outcome,
        verification=verification,
        confidence_level=_confidence_level(score),
        crop_name=current_crop,
        growth_stage_name=growth_stage.name if growth_stage else None,
        farm_problem=problem,
        problem_sync=problem_sync,
        message=message,
        disclaimer=DISCLAIMER,
    )


@router.post(
    "/{farmland_id}/disease-results/{disease_result_id}/sync-problem",
    response_model=DiseaseProblemSyncResponse,
)
def retry_disease_problem_sync(
    farmland_id: UUID,
    disease_result_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
    gateway: M3Gateway,
) -> DiseaseProblemSyncResponse:
    """Retry a saved issue's Module 3 write without uploading or analyzing its photo again."""
    _ = farmer_id
    _get_state(gateway, farmland_id)  # Verify ownership before acquiring the database row lock.
    _lock_farmland_problem_sync(db, farmland_id)
    farm_state = _get_state(gateway, farmland_id)
    result = db.scalar(
        select(DiseaseResult).where(
            DiseaseResult.id == disease_result_id,
            DiseaseResult.farmland_id == farmland_id,
        ).with_for_update()
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Disease result not found for this farm.")

    details = dict(result.model_details)
    if details.get("outcome") != "possible_disease":
        raise HTTPException(
            status_code=409,
            detail="Only a possible crop issue can be recorded as a farm problem.",
        )

    crop_name = db.scalar(select(Crop.name).where(Crop.id == result.crop_id))
    recorded_status = details.get("problem_sync")
    if recorded_status in {"created", "reused"}:
        linked_id = details.get("farm_problem_id")
        linked_problem = next(
            (problem for problem in farm_state.open_problems if str(problem.id) == linked_id),
            None,
        )
        return DiseaseProblemSyncResponse(
            disease_result=_result_read(result, crop_name),
            farm_problem=linked_problem,
            problem_sync=recorded_status,
            message="This result was already linked to Module 3; no duplicate problem was created.",
        )

    active_season = farm_state.active_season
    if active_season is None or active_season.id != result.season_id:
        raise HTTPException(
            status_code=409,
            detail="The result belongs to a previous crop season. Check the current crop before retrying.",
        )

    prediction_label = details.get("prediction_label")
    if not isinstance(prediction_label, str) or not result.possible_issue or result.season_id is None:
        raise HTTPException(status_code=409, detail="The saved result is missing its problem details.")

    category = _category_for_label(prediction_label)
    score = float(result.confidence) if result.confidence is not None else 0.0
    description = (
        "DiseaseResult " + str(result.id) + ": possible " + result.possible_issue
        + "; model score " + format(score, ".2f") + "."
    )
    stage_name = details.get("growth_stage_name")
    if isinstance(stage_name, str) and stage_name:
        description += " Growth stage: " + stage_name + "."

    try:
        problem, problem_sync = _sync_open_problem(
            gateway,
            farmland_id,
            result.season_id,
            category,
            description,
            farm_state.open_problems,
        )
    except Module3ClientError:
        logger.exception("Module 3 problem retry failed for disease result %s", result.id)
        problem = None
        problem_sync = "failed"
        message = "The result remains saved, but Module 3 is still unavailable. Try again later."
    else:
        details["problem_sync"] = problem_sync
        details["farm_problem_id"] = str(problem.id)
        result.model_details = details
        db.commit()
        db.refresh(result)
        message = (
            "The farm problem was created."
            if problem_sync == "created"
            else "A matching open farm problem already exists."
        )

    return DiseaseProblemSyncResponse(
        disease_result=_result_read(result, crop_name),
        farm_problem=problem,
        problem_sync=problem_sync,
        message=message,
    )


@router.get(
    "/{farmland_id}/disease-results",
    response_model=list[DiseaseResultRead],
)
def list_disease_results(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
    gateway: M3Gateway,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DiseaseResultRead]:
    _ = farmer_id
    _get_state(gateway, farmland_id)
    rows = db.execute(
        select(DiseaseResult, Crop.name)
        .outerjoin(Crop, Crop.id == DiseaseResult.crop_id)
        .where(DiseaseResult.farmland_id == farmland_id)
        .order_by(DiseaseResult.created_at.desc(), DiseaseResult.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        DiseaseResultRead.model_validate(result).model_copy(update={"crop_name": crop_name})
        for result, crop_name in rows
    ]

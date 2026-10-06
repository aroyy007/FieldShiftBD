"""M2 evidence retrieval over the shared AgriculturalKnowledge model.

This provider filters and structures evidence. It does not score crops or make
recommendations. Synthetic records belong in tests only.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.core import AgriculturalKnowledge


class EvidenceStatus(StrEnum):
    AVAILABLE = "available"
    MISSING_EVIDENCE = "missing_approved_effective_evidence"


@dataclass(frozen=True)
class KnowledgeQuery:
    """Context for retrieving reviewed knowledge relevant to one crop."""

    crop_id: UUID
    crop_variety_id: UUID | None = None
    factor: str | None = None
    categories: frozenset[str] = field(default_factory=frozenset)
    region_codes: frozenset[str] = field(default_factory=frozenset)
    context: Mapping[str, Any] = field(default_factory=dict)
    as_of: date = field(default_factory=date.today)


@dataclass(frozen=True)
class AgriculturalEvidence:
    """Structured, provenance-preserving evidence passed to M2 reasoning."""

    id: UUID
    crop_id: UUID | None
    crop_variety_id: UUID | None
    category: str
    factor: str
    conditions: Mapping[str, Any] | None
    value: Any
    region_code: str | None
    context: Mapping[str, Any]
    content: Mapping[str, Any]
    source_name: str
    source_type: str
    source_reference: str | None
    review_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    effective_from: date | None
    effective_to: date | None


@dataclass(frozen=True)
class KnowledgeResult:
    status: EvidenceStatus
    items: tuple[AgriculturalEvidence, ...]
    as_of: date
    message: str


def _source_type(row: AgriculturalKnowledge) -> str | None:
    """Source type is M2 metadata in JSON because the shared model has no column."""
    content = row.content if isinstance(row.content, dict) else {}
    value = content.get("source_type")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if "in" in expected:
            return _value_matches(actual, expected["in"])
        try:
            number = Decimal(str(actual))
            if "min" in expected and number < Decimal(str(expected["min"])):
                return False
            if "max" in expected and number > Decimal(str(expected["max"])):
                return False
            return "min" in expected or "max" in expected
        except (InvalidOperation, TypeError, ValueError):
            return False
    allowed = expected if isinstance(expected, list) else [expected]
    for candidate in allowed:
        if isinstance(actual, str) and isinstance(candidate, str):
            if actual.strip().casefold() == candidate.strip().casefold():
                return True
        elif actual == candidate:
            return True
    return False


def _conditions_match(conditions: Any, context: Mapping[str, Any]) -> bool:
    if conditions is None:
        return True
    if not isinstance(conditions, dict):
        return False
    for key, expected in conditions.items():
        if key not in context or context[key] is None:
            return False
        if not _value_matches(context[key], expected):
            return False
    return True


_CONTEXT_LISTS = {
    "suitable_because",
    "positive_factors",
    "limiting_factors",
    "risks_or_concerns",
    "concerns",
}


def _filter_content(content: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any] | None:
    filtered = deepcopy(dict(content))
    applicability = filtered.get("applicability")
    if applicability is not None and not _conditions_match(applicability, context):
        return None
    for key in _CONTEXT_LISTS:
        value = filtered.get(key)
        if not isinstance(value, list):
            continue
        filtered[key] = [
            item for item in value
            if not isinstance(item, dict) or _conditions_match(item.get("when"), context)
        ]
    factors = filtered.get("factors")
    if isinstance(factors, dict):
        kept = {}
        for name, item in factors.items():
            if isinstance(item, dict) and item.get("when") is not None:
                if not _conditions_match(item.get("when"), context):
                    continue
            kept[name] = item
        filtered["factors"] = kept
    return filtered


def _row_matches_query(row: AgriculturalKnowledge, query: KnowledgeQuery) -> bool:
    if row.review_status != "approved":
        return False
    if row.effective_from is not None and row.effective_from > query.as_of:
        return False
    if row.effective_to is not None and row.effective_to < query.as_of:
        return False
    if row.crop_id is not None and row.crop_id != query.crop_id:
        return False
    if row.crop_variety_id is not None and row.crop_variety_id != query.crop_variety_id:
        return False
    if query.categories and row.category not in query.categories:
        return False
    if query.factor is not None:
        content = row.content if isinstance(row.content, dict) else {}
        declared_factor = content.get("factor")
        if query.factor != row.category and query.factor != declared_factor:
            return False
    if query.region_codes:
        normalized = {code.strip().casefold() for code in query.region_codes}
        if row.region_code is not None and row.region_code.strip().casefold() not in normalized:
            return False
    elif row.region_code is not None:
        return False
    if _source_type(row) is None:
        return False
    return True


def _to_evidence(row: AgriculturalKnowledge, content: Mapping[str, Any]) -> AgriculturalEvidence:
    source_type = _source_type(row)
    assert source_type is not None  # Enforced by _row_matches_query.
    declared_factor = content.get("factor")
    applicability = content.get("applicability")
    evidence_value = content.get("evidence", content.get("value"))
    return AgriculturalEvidence(
        id=row.id,
        crop_id=row.crop_id,
        crop_variety_id=row.crop_variety_id,
        category=row.category,
        factor=declared_factor if isinstance(declared_factor, str) else row.category,
        conditions=applicability if isinstance(applicability, dict) else None,
        value=evidence_value,
        region_code=row.region_code,
        context=dict(content.get("context", {})) if isinstance(content.get("context"), dict) else {},
        content=content,
        source_name=row.source_name,
        source_type=source_type,
        source_reference=row.source_reference,
        review_status=row.review_status,
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
    )


def get_relevant_evidence(db: Session, query: KnowledgeQuery) -> KnowledgeResult:
    """Return only approved, effective, crop/context-relevant structured evidence."""
    statement = select(AgriculturalKnowledge).where(
        AgriculturalKnowledge.review_status == "approved",
        or_(AgriculturalKnowledge.crop_id == query.crop_id, AgriculturalKnowledge.crop_id.is_(None)),
        or_(AgriculturalKnowledge.crop_variety_id.is_(None),
            AgriculturalKnowledge.crop_variety_id == query.crop_variety_id)
        if query.crop_variety_id is not None
        else AgriculturalKnowledge.crop_variety_id.is_(None),
        or_(AgriculturalKnowledge.effective_from.is_(None),
            AgriculturalKnowledge.effective_from <= query.as_of),
        or_(AgriculturalKnowledge.effective_to.is_(None),
            AgriculturalKnowledge.effective_to >= query.as_of),
    )
    if query.categories:
        statement = statement.where(AgriculturalKnowledge.category.in_(query.categories))
    rows = db.scalars(statement)
    items = []
    for row in rows:
        if not _row_matches_query(row, query):
            continue
        content = row.content if isinstance(row.content, dict) else {}
        relevant_content = _filter_content(content, query.context)
        if relevant_content is None:
            continue
        items.append(_to_evidence(row, relevant_content))
    items.sort(key=lambda item: (item.category, str(item.crop_variety_id or ""), str(item.id)))
    return KnowledgeResult(
        status=EvidenceStatus.AVAILABLE if items else EvidenceStatus.MISSING_EVIDENCE,
        items=tuple(items),
        as_of=query.as_of,
        message=(
            "Reviewed and currently effective evidence is available."
            if items
            else "No approved, currently effective evidence applies to this crop and context."
        ),
    )

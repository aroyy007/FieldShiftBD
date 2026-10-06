from typing import Protocol
from uuid import UUID

import httpx
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import settings
from app.schemas.farm_state import FarmStateRead, ProblemCreate, ProblemRead


class Module3ClientError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Module3Gateway(Protocol):
    def read_farm_state(self, farmland_id: UUID) -> FarmStateRead:
        ...

    def create_problem(self, farmland_id: UUID, payload: ProblemCreate) -> ProblemRead:
        ...


class Module3ApiClient:
    """HTTP adapter for Module 3's existing farm-state and problem contracts."""

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers or {},
            timeout=httpx.Timeout(5.0, connect=2.0),
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def read_farm_state(self, farmland_id: UUID) -> FarmStateRead:
        response = self._request("GET", "/farmlands/" + str(farmland_id) + "/state")
        try:
            return FarmStateRead.model_validate(response.json())
        except (ValidationError, ValueError) as error:
            raise Module3ClientError(503, "Module 3 returned an invalid farm-state response") from error

    def create_problem(self, farmland_id: UUID, payload: ProblemCreate) -> ProblemRead:
        response = self._request(
            "POST",
            "/farmlands/" + str(farmland_id) + "/problems",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        try:
            return ProblemRead.model_validate(response.json())
        except (ValidationError, ValueError) as error:
            raise Module3ClientError(503, "Module 3 returned an invalid problem response") from error

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.RequestError as error:
            raise Module3ClientError(503, "Module 3 is temporarily unavailable") from error

        if response.is_success:
            return response

        if response.status_code >= 500:
            raise Module3ClientError(503, "Module 3 is temporarily unavailable")

        detail = "Module 3 rejected the request"
        try:
            body = response.json()
            if isinstance(body, dict) and body.get("detail") is not None:
                detail = str(body["detail"])
        except ValueError:
            pass
        raise Module3ClientError(response.status_code, detail)


def get_module3_gateway(request: Request):
    """Create an authenticated, request-scoped client for the M3 API."""
    forwarded_headers = {}
    for header_name in ("authorization", "cookie"):
        value = request.headers.get(header_name)
        if value:
            forwarded_headers[header_name] = value

    gateway = Module3ApiClient(
        base_url=settings.MODULE3_API_BASE_URL,
        headers=forwarded_headers,
    )
    try:
        yield gateway
    finally:
        gateway.close()

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.models import Entry, EntryCreate, EntryUpdate, ReadingStatus

# ============================================================================
# Secure Logging Configuration (P06 - C3)
# Logs without PII, only safe diagnostic information
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("reading_list_api")


# ============================================================================
# Security Headers Middleware (P06 - C1, Risk R03)
# Protects against XSS, clickjacking, MIME sniffing
# ============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses (OWASP recommendations)"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent XSS attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cache control for sensitive data
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        return response


# ============================================================================
# Request Body Size Limit Middleware (P06 - C1, Risk R09, NFR-008)
# Protects against oversized payload DoS attacks
# ============================================================================

MAX_BODY_SIZE = 64 * 1024  # 64 KB limit


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks"""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length:
            if int(content_length) > MAX_BODY_SIZE:
                logger.warning(
                    f"Request rejected: body size {content_length} exceeds limit {MAX_BODY_SIZE}"
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "type": "/errors/payload-too-large",
                        "title": "Payload Too Large",
                        "status": 413,
                        "detail": f"Request body exceeds max size of {MAX_BODY_SIZE} bytes",
                        "correlation_id": str(uuid4()),
                    },
                    media_type="application/problem+json",
                )

        return await call_next(request)


# Rate Limiter configuration (NFR-004, Risk R01)
# Limit: 100 requests per minute per IP address
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="SecDev Course App", version="0.1.0")

# Add security middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# RFC 7807 Problem Details Error Format (ADR-002)
# ============================================================================


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details for HTTP APIs"""

    type: str = Field(default="about:blank", description="URI reference for error type")
    title: str = Field(..., description="Short human-readable summary")
    status: int = Field(..., description="HTTP status code")
    detail: Optional[str] = Field(None, description="Human-readable explanation")
    instance: Optional[str] = Field(None, description="URI reference for occurrence")
    correlation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique ID for tracing in logs",
    )


class ApiError(Exception):
    """Application-level error with RFC 7807 support"""

    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    """Handle ApiError with RFC 7807 Problem Details format"""
    problem = ProblemDetail(
        type=f"/errors/{exc.code}",
        title=exc.code.replace("_", " ").title(),
        status=exc.status,
        detail=exc.message,
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException with RFC 7807 format"""
    detail = exc.detail if isinstance(exc.detail, str) else "An error occurred"
    problem = ProblemDetail(
        type="/errors/http-error",
        title="HTTP Error",
        status=exc.status_code,
        detail=detail,
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}

# Reading List database
_READING_LIST_DB = {"entries": [], "next_id": 1}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


# ============================================================================
# Reading List CRUD Endpoints
# ============================================================================


@app.post("/entries", response_model=Entry, status_code=201)
@limiter.limit("100/minute")
def create_entry(request: Request, entry_data: EntryCreate):
    """Создать новую запись в списке для чтения"""
    now = datetime.now(timezone.utc)
    entry = Entry(
        id=_READING_LIST_DB["next_id"],
        title=entry_data.title,
        author=entry_data.author,
        status=entry_data.status,
        notes=entry_data.notes,
        created_at=now,
        updated_at=now,
    )
    _READING_LIST_DB["entries"].append(entry)
    _READING_LIST_DB["next_id"] += 1

    # Secure logging without PII (P06-C3, NFR-007)
    logger.info(f"CREATE_ENTRY | id={entry.id} | status={entry.status}")

    return entry


@app.get("/entries", response_model=List[Entry])
@limiter.limit("100/minute")
def get_entries(request: Request):
    """Получить все записи из списка для чтения"""
    return _READING_LIST_DB["entries"]


@app.get("/entries/{entry_id}", response_model=Entry)
@limiter.limit("100/minute")
def get_entry(request: Request, entry_id: int):
    """Получить запись по ID"""
    for entry in _READING_LIST_DB["entries"]:
        if entry.id == entry_id:
            return entry
    raise ApiError(code="not_found", message=f"Entry {entry_id} not found", status=404)


@app.put("/entries/{entry_id}", response_model=Entry)
@limiter.limit("100/minute")
def update_entry(request: Request, entry_id: int, entry_data: EntryUpdate):
    """Обновить существующую запись"""
    for i, entry in enumerate(_READING_LIST_DB["entries"]):
        if entry.id == entry_id:
            # Обновляем только переданные поля
            update_dict = entry_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.now(timezone.utc)

            updated_entry = entry.model_copy(update=update_dict)
            _READING_LIST_DB["entries"][i] = updated_entry

            # Secure logging without PII (P06-C3, NFR-007)
            logger.info(
                f"UPDATE_ENTRY | id={entry_id} | fields={list(update_dict.keys())}"
            )

            return updated_entry

    raise ApiError(code="not_found", message=f"Entry {entry_id} not found", status=404)


@app.delete("/entries/{entry_id}", status_code=204)
@limiter.limit("100/minute")
def delete_entry(request: Request, entry_id: int):
    """Удалить запись из списка"""
    for i, entry in enumerate(_READING_LIST_DB["entries"]):
        if entry.id == entry_id:
            _READING_LIST_DB["entries"].pop(i)

            # Secure logging without PII (P06-C3, NFR-007)
            logger.info(f"DELETE_ENTRY | id={entry_id}")

            return
    raise ApiError(code="not_found", message=f"Entry {entry_id} not found", status=404)


@app.get("/entries/filter/by-status", response_model=List[Entry])
@limiter.limit("100/minute")
def filter_entries_by_status(
    request: Request,
    status: Optional[ReadingStatus] = None,
    author: Optional[str] = None,
):
    """Фильтрация записей по статусу и/или автору"""
    result = _READING_LIST_DB["entries"]

    if status:
        result = [e for e in result if e.status == status]

    if author:
        result = [e for e in result if author.lower() in e.author.lower()]

    return result

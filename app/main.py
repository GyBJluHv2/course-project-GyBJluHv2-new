from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.models import Entry, EntryCreate, EntryUpdate, ReadingStatus

# Rate Limiter configuration (NFR-004, Risk R01)
# Limit: 100 requests per minute per IP address
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="SecDev Course App", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
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
            return updated_entry

    raise ApiError(code="not_found", message=f"Entry {entry_id} not found", status=404)


@app.delete("/entries/{entry_id}", status_code=204)
@limiter.limit("100/minute")
def delete_entry(request: Request, entry_id: int):
    """Удалить запись из списка"""
    for i, entry in enumerate(_READING_LIST_DB["entries"]):
        if entry.id == entry_id:
            _READING_LIST_DB["entries"].pop(i)
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

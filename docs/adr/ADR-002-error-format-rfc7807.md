# ADR-002: Error Response Format (RFC 7807)

**Status:** Accepted
**Date:** 2024-12-09
**Decision Makers:** Development Team

---

## Context

Reading List API должен возвращать понятные и стандартизированные ошибки. Текущая реализация использует кастомный формат:

```json
{
  "error": {
    "code": "not_found",
    "message": "Entry 42 not found"
  }
}
```

Проблемы текущего подхода:
- Нестандартный формат (не совместим с клиентскими библиотеками)
- Отсутствует `correlation_id` для трассировки
- Нет типизации ошибок (URI для документации)
- Риск утечки внутренних деталей (stack traces)

### Связь с предыдущими практиками
- **NFR-007** (P03): Логирование операций
- **T07** (P04): Утечка через ошибки (stack trace)
- **R06** (P04): Утечка stack trace в ответах API

---

## Decision

**Внедряем RFC 7807 (Problem Details for HTTP APIs) формат ошибок:**

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Entry with ID 42 was not found",
  "instance": "/entries/42",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Структура RFC 7807

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `type` | URI | ✅ | URI идентификатор типа ошибки |
| `title` | string | ✅ | Краткое описание типа ошибки |
| `status` | integer | ✅ | HTTP status code |
| `detail` | string | ❌ | Детальное описание конкретной ошибки |
| `instance` | URI | ❌ | URI конкретного ресурса |
| `correlation_id` | string | ❌ | UUID для трассировки в логах |

### Реализация

```python
from uuid import uuid4
from fastapi import Request
from fastapi.responses import JSONResponse

class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))

async def problem_exception_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content=ProblemDetail(
            type=f"/errors/{exc.code}",
            title=exc.code.replace("_", " ").title(),
            status=exc.status,
            detail=exc.message,
            instance=str(request.url.path),
        ).model_dump(),
        media_type="application/problem+json",
    )
```

---

## Alternatives

### Alternative 1: Keep Custom Format

**Описание:** Оставить текущий `{"error": {"code": ..., "message": ...}}` формат.

**Плюсы:**
- Не требует изменений
- Простой формат

**Минусы:**
- Нестандартный
- Нет correlation_id
- Несовместим с клиентскими библиотеками

**Причина отказа:** Не соответствует best practices, нет трассировки.

---

### Alternative 2: Google Error Format

**Описание:** Использовать Google API error format.

```json
{
  "error": {
    "code": 404,
    "message": "Not found",
    "errors": [{"domain": "...", "reason": "..."}]
  }
}
```

**Плюсы:**
- Хорошо документирован
- Используется в Google APIs

**Минусы:**
- Проприетарный формат
- Более сложная структура
- Нет широкой поддержки в клиентских библиотеках

**Причина отказа:** RFC 7807 — открытый стандарт с большей поддержкой.

---

### Alternative 3: RFC 7807 Problem Details ✅ (Выбрано)

**Описание:** Стандарт IETF для представления ошибок в HTTP API.

**Плюсы:**
- Открытый стандарт (IETF RFC)
- Поддержка в клиентских библиотеках (многие языки)
- Расширяемый (можно добавлять кастомные поля)
- `correlation_id` для трассировки
- Content-Type: `application/problem+json`

**Минусы:**
- Требует миграции существующих клиентов
- Немного более verbose

---

## Consequences

### Положительные

1. **Стандартизация**: Совместимость с клиентскими библиотеками
2. **Трассировка**: `correlation_id` связывает ошибку с логами
3. **Безопасность**: Маскирование внутренних деталей
4. **Документация**: URI типов ошибок ведут к документации

### Отрицательные

1. **Breaking Change**: Клиенты должны обновить парсинг ошибок
2. **Миграция**: Нужно обновить все error handlers

### Нейтральные

- Размер response немного увеличится

---

## Security Impact

### Закрываемые угрозы

| Угроза | STRIDE | Риск | Статус |
|--------|--------|------|--------|
| T07: Утечка stack trace | Info Disclosure | R06 | ✅ Митигирован |
| T11: Отсутствие аудита | Repudiation | R04 | ✅ Митигирован (correlation_id) |

### Принципы безопасности

1. **Никогда** не включать stack traces в production
2. **Маскировать** внутренние ID и пути
3. **Логировать** correlation_id для расследования
4. **Не раскрывать** информацию о системе (версии, пути)

### Пример маскирования

❌ Плохо:
```json
{
  "detail": "SQLAlchemyError: connection refused to postgres:5432"
}
```

✅ Хорошо:
```json
{
  "type": "/errors/internal-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please try again later.",
  "correlation_id": "abc-123"
}
```

---

## Rollout Plan

### Phase 1: Implementation ✅
- [x] Создать ProblemDetail Pydantic model
- [x] Обновить exception handlers
- [x] Добавить correlation_id генерацию

### Phase 2: Testing
- [x] Тесты на формат ошибок
- [x] Тесты на correlation_id
- [ ] Integration tests

### Phase 3: Documentation
- [ ] Документировать типы ошибок в OpenAPI
- [ ] Создать error catalog

### Definition of Done

- [x] Все ошибки возвращают RFC 7807 формат
- [x] correlation_id присутствует в каждой ошибке
- [x] Stack traces не попадают в response (production)
- [x] Тесты на формат ошибок проходят

### Feature Flag

```python
# Для постепенного rollout
USE_RFC7807_ERRORS = os.getenv("USE_RFC7807_ERRORS", "true") == "true"
```

---

## Links

- **RFC 7807:** https://datatracker.ietf.org/doc/html/rfc7807
- **NFR Reference:** NFR-007 (Логирование операций)
- **Threat Model:** T07, T11 (STRIDE.md)
- **Risk Register:** R04, R06 (RISKS.md)
- **Tests:** `tests/test_errors.py`
- **Implementation:** `app/main.py`


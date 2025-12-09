# ADR-001: Input Validation Strategy

**Status:** Accepted
**Date:** 2024-12-09
**Decision Makers:** Development Team

---

## Context

Reading List API принимает пользовательский ввод для создания и обновления записей о книгах. Без надлежащей валидации система уязвима к:

- **Injection атакам** (SQL, NoSQL, XSS)
- **Buffer overflow** через длинные строки
- **Data corruption** от невалидных данных
- **DoS** через oversized payloads

Текущая ситуация:
- Используется FastAPI с Pydantic для базовой валидации
- Ограничения длины полей уже установлены в моделях
- Нет явной санитизации HTML/специальных символов

### Связь с предыдущими практиками
- **NFR-003** (P03): Валидация входных данных — 100% запросов валидируются
- **T05, T09** (P04): SQL Injection, XSS payload
- **R02, R03** (P04): Риски injection атак

---

## Decision

**Используем многоуровневую валидацию ввода:**

1. **Pydantic Models** — первичная валидация типов и ограничений
2. **Field Constraints** — строгие лимиты на длину и формат
3. **Enum Types** — ограничение допустимых значений статусов
4. **Custom Validators** — для сложных проверок (при необходимости)

### Реализация

```python
class EntryCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Название книги/статьи"
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Автор"
    )
    status: ReadingStatus = Field(
        default=ReadingStatus.TO_READ,
        description="Статус прочтения"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Заметки"
    )
```

### Правила валидации

| Поле | Тип | Min | Max | Обязательное | Примечание |
|------|-----|-----|-----|--------------|------------|
| title | str | 1 | 200 | ✅ | Название книги |
| author | str | 1 | 100 | ✅ | Имя автора |
| status | enum | - | - | ❌ | to_read/reading/completed |
| notes | str | 0 | 1000 | ❌ | Заметки пользователя |

---

## Alternatives

### Alternative 1: Manual Validation in Endpoints

**Описание:** Проверка данных вручную в каждом endpoint.

**Плюсы:**
- Полный контроль над логикой валидации
- Кастомные сообщения об ошибках

**Минусы:**
- Дублирование кода
- Легко пропустить проверку
- Сложнее поддерживать

**Причина отказа:** Нарушает DRY, увеличивает риск ошибок.

---

### Alternative 2: JSON Schema Validation

**Описание:** Использование JSON Schema для валидации входящих запросов.

**Плюсы:**
- Стандартный формат
- Может использоваться для документации

**Минусы:**
- Требует дополнительной зависимости
- Менее интегрирован с FastAPI
- Не генерирует автоматически OpenAPI spec

**Причина отказа:** Pydantic уже интегрирован с FastAPI и генерирует OpenAPI.

---

### Alternative 3: Pydantic with Strict Mode ✅ (Выбрано)

**Описание:** Использование Pydantic models с строгими ограничениями.

**Плюсы:**
- Нативная интеграция с FastAPI
- Автоматическая генерация OpenAPI документации
- Type hints для IDE
- Понятные сообщения об ошибках
- Высокая производительность

**Минусы:**
- Ограничен Python экосистемой
- Сложные валидации требуют кастомных validators

---

## Consequences

### Положительные

1. **Безопасность**: Автоматическое отклонение невалидных данных
2. **Консистентность**: Единообразная валидация во всех endpoints
3. **Документация**: OpenAPI spec генерируется автоматически
4. **Developer Experience**: Type hints и autocompletion в IDE

### Отрицательные

1. **Производительность**: Небольшой overhead на валидацию (незначительный)
2. **Сложность**: Кастомные валидаторы требуют изучения Pydantic API

### Нейтральные

- Сообщения об ошибках на английском (стандарт для API)

---

## Security Impact

### Закрываемые угрозы

| Угроза | STRIDE | Риск | Статус |
|--------|--------|------|--------|
| T05: SQL Injection | Tampering | R02 | ✅ Митигирован |
| T09: XSS payload | Tampering | R03 | ⚠️ Частично (нужен CSP) |
| T10: Oversized payload | Tampering | R09 | ✅ Митигирован |
| T12: Mass assignment | EoP | R08 | ✅ Митигирован |

### Остаточные риски

- XSS при отображении данных (требуется output encoding на фронтенде)
- Logical injection (например, в notes поле)

---

## Rollout Plan

### Phase 1: Current State ✅
- [x] Pydantic models с базовыми ограничениями
- [x] Тесты валидации (`test_create_entry_validation_error`)

### Phase 2: Enhancement
- [ ] Добавить regex-паттерны для author (только буквы и пробелы)
- [ ] Rate limiting для /entries endpoints (реализовано в P04)

### Phase 3: Advanced
- [ ] Content-Type validation
- [ ] Request size limit middleware (NFR-008)

### Definition of Done

- [x] Все поля имеют ограничения min/max length
- [x] Enum для status (to_read, reading, completed)
- [x] Тесты на невалидные данные проходят
- [x] CI pipeline green

---

## Links

- **NFR Reference:** NFR-003 (Валидация входных данных)
- **Threat Model:** T05, T09, T10, T12 (STRIDE.md)
- **Risk Register:** R02, R03, R08, R09 (RISKS.md)
- **Tests:** `tests/test_reading_list.py::test_create_entry_validation_error`
- **Implementation:** `app/models.py`

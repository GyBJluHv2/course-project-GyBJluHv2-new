# STRIDE Threat Analysis — Reading List API

## Обзор

Данный документ содержит анализ угроз по методологии STRIDE для сервиса Reading List API.

**STRIDE категории:**
- **S**poofing — Подмена идентичности
- **T**ampering — Изменение данных
- **R**epudiation — Отказ от авторства
- **I**nformation Disclosure — Раскрытие информации
- **D**enial of Service — Отказ в обслуживании
- **E**levation of Privilege — Повышение привилегий

---

## Таблица угроз STRIDE

| ID | Поток/Элемент | Категория | Угроза | Описание | Контроль | NFR | Приоритет |
|----|---------------|-----------|--------|----------|----------|-----|-----------|
| **T01** | F1: Client Request | **S** (Spoofing) | Подмена клиента | Атакующий отправляет запросы от имени легитимного пользователя | API Key / JWT токены | NFR-003 | High |
| **T02** | F1: Client Request | **T** (Tampering) | Модификация запроса (MITM) | Перехват и изменение данных в транзите | TLS 1.3, HSTS | NFR-002 | Critical |
| **T03** | F1: Client Request | **D** (DoS) | DDoS-атака | Массовая отправка запросов для перегрузки сервера | Rate Limiting (100 req/min) | NFR-004 | Critical |
| **T04** | F2: Forward Request | **I** (Info Disclosure) | Утечка заголовков | Внутренние заголовки (X-Internal-*) попадают к клиенту | Header sanitization | NFR-007 | Medium |
| **T05** | F3: Database Query | **T** (Tampering) | SQL Injection | Внедрение SQL через поля title/author/notes | Pydantic + ORM (parameterized queries) | NFR-003 | Critical |
| **T06** | F3: Database Query | **I** (Info Disclosure) | Извлечение данных | Несанкционированный доступ к чужим записям | Row-level security (будущее) | NFR-003 | High |
| **T07** | F4: DB Response | **I** (Info Disclosure) | Утечка через ошибки | Stack trace в ответе при ошибке БД | Custom error handler | NFR-007 | Medium |
| **T08** | F5: API Response | **I** (Info Disclosure) | Избыточные данные | Возврат внутренних полей (id, timestamps) | Response model filtering | NFR-006 | Low |
| **T09** | Input Validator | **T** (Tampering) | XSS payload | Внедрение скриптов в поля title/notes | Input sanitization, CSP headers | NFR-003 | High |
| **T10** | Input Validator | **T** (Tampering) | Oversized payload | Отправка огромного body для исчерпания памяти | Max body size (64KB) | NFR-008 | Medium |
| **T11** | CRUD Handler | **R** (Repudiation) | Отсутствие аудита | Пользователь отрицает выполнение действия | Audit logging (NFR-007) | NFR-007 | High |
| **T12** | CRUD Handler | **E** (EoP) | Mass assignment | Изменение защищённых полей (id, created_at) | Pydantic explicit fields | NFR-003 | High |
| **T13** | Rate Limiter | **D** (DoS) | Bypass rate limit | Обход лимита через разные IP/headers | IP + fingerprint limiting | NFR-004 | Medium |
| **T14** | Audit Logger | **R** (Repudiation) | Log injection | Внедрение ложных записей в логи | Log sanitization | NFR-007 | Medium |
| **T15** | Database | **I** (Info Disclosure) | Backup exposure | Утечка backup файлов БД | Encryption at rest | NFR-005 | High |

---

## Детальный анализ ключевых угроз

### T01: Spoofing — Подмена клиента

**Поток:** F1 (Client → Load Balancer)

**Сценарий атаки:**
1. Атакующий перехватывает или угадывает идентификатор сессии
2. Отправляет запросы от имени жертвы
3. Получает доступ к чужому списку чтения

**Контроли:**
- [ ] JWT токены с коротким TTL (15 мин)
- [ ] Refresh token rotation
- [x] HTTPS обязателен (TLS termination)

**Связь с NFR:** NFR-003 (Валидация входных данных)

---

### T03: DoS — DDoS-атака

**Поток:** F1 (Client → Load Balancer)

**Сценарий атаки:**
1. Атакующий генерирует тысячи запросов в секунду
2. Сервер перегружен, легитимные пользователи не могут работать
3. Возможен каскадный отказ (БД, память)

**Контроли:**
- [x] Rate Limiting: 100 req/min на IP (NFR-004)
- [ ] WAF правила
- [ ] CloudFlare/AWS Shield (для prod)

**Связь с NFR:** NFR-004 (Rate Limiting)

---

### T05: Tampering — SQL Injection

**Поток:** F3 (API → Database)

**Сценарий атаки:**
```
POST /entries
{
  "title": "'; DROP TABLE entries; --",
  "author": "Attacker"
}
```

**Контроли:**
- [x] Pydantic валидация длины и формата
- [x] ORM (SQLAlchemy) с parameterized queries
- [x] Тесты на injection (test_reading_list.py)

**Связь с NFR:** NFR-003 (Валидация входных данных)

**Проверка:** BDD сценарий 3.4 в NFR_BDD.md

---

### T09: Tampering — XSS payload

**Поток:** Input Validator

**Сценарий атаки:**
```
POST /entries
{
  "title": "<script>alert('xss')</script>",
  "author": "Attacker"
}
```

**Контроли:**
- [x] Pydantic не выполняет экранирование (данные хранятся as-is)
- [ ] CSP headers для фронтенда
- [ ] Output encoding при отображении

**Связь с NFR:** NFR-003 (Валидация входных данных)

**Проверка:** BDD сценарий 3.3 в NFR_BDD.md

---

### T11: Repudiation — Отсутствие аудита

**Элемент:** CRUD Handler

**Сценарий:**
1. Пользователь удаляет важную запись
2. Заявляет, что не делал этого
3. Нет доказательств действия

**Контроли:**
- [x] Audit logging всех CREATE/UPDATE/DELETE (NFR-007)
- [x] Timestamp + action type в логах
- [ ] Immutable log storage

**Связь с NFR:** NFR-007 (Логирование операций)

---

## Матрица STRIDE по элементам

| Элемент/Поток | S | T | R | I | D | E |
|---------------|---|---|---|---|---|---|
| F1: Client Request | T01 | T02 | — | — | T03 | — |
| F2: Forward Request | — | — | — | T04 | — | — |
| F3: Database Query | — | T05 | — | T06 | — | — |
| F4: DB Response | — | — | — | T07 | — | — |
| F5: API Response | — | — | — | T08 | — | — |
| Input Validator | — | T09, T10 | — | — | — | — |
| CRUD Handler | — | — | T11 | — | — | T12 |
| Rate Limiter | — | — | — | — | T13 | — |
| Audit Logger | — | — | T14 | — | — | — |
| Database | — | — | — | T15 | — | — |

---

## Исключения (Не применимо)

| Элемент | Категория | Обоснование |
|---------|-----------|-------------|
| Health endpoint | Spoofing | Публичный endpoint, не требует аутентификации |
| GET /entries | Repudiation | Чтение не требует аудита (только запись) |
| In-memory DB (dev) | Info Disclosure (backup) | Нет персистентного хранения в dev-режиме |

---

## История изменений

| Дата | Версия | Автор | Изменения |
|------|--------|-------|-----------|
| 2024-12-09 | 1.0 | Атаханов Н.Р. | Первоначальная версия STRIDE |


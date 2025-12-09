# Risk Register — Reading List API

## Обзор

Данный документ содержит реестр рисков безопасности для сервиса Reading List API, основанный на STRIDE-анализе.

**Шкала оценки:**
- **L (Likelihood)**: 1-5 (1 = редко, 5 = почти наверняка)
- **I (Impact)**: 1-5 (1 = минимальный, 5 = критический)
- **Risk Score**: L × I (1-25)

**Уровни риска:**
- 🟢 **Low** (1-6): Принять или отложить
- 🟡 **Medium** (7-12): Планировать митигацию
- 🔴 **High** (13-19): Срочно снизить
- ⚫ **Critical** (20-25): Немедленно устранить

---

## Реестр рисков

| ID | Риск | Угроза (STRIDE) | L | I | Score | Уровень | Стратегия | Контроль | Владелец | Срок | Статус |
|----|------|-----------------|---|---|-------|---------|-----------|----------|----------|------|--------|
| **R01** | DDoS-атака выводит сервис из строя | T03 (DoS) | 4 | 5 | 20 | ⚫ Critical | Снизить | Rate Limiting 100 req/min | @developer | Sprint 1 | 🔄 В работе |
| **R02** | SQL Injection приводит к утечке данных | T05 (Tampering) | 2 | 5 | 10 | 🟡 Medium | Снизить | Pydantic + ORM | @developer | Sprint 1 | ✅ Закрыт |
| **R03** | XSS-атака через поля записей | T09 (Tampering) | 3 | 4 | 12 | 🟡 Medium | Снизить | CSP headers, sanitization | @developer | Sprint 2 | 📋 План |
| **R04** | Отсутствие аудита — невозможность расследования | T11 (Repudiation) | 3 | 4 | 12 | 🟡 Medium | Снизить | Structured logging | @developer | Sprint 2 | 📋 План |
| **R05** | MITM-атака на незащищённом канале | T02 (Tampering) | 2 | 5 | 10 | 🟡 Medium | Снизить | TLS 1.3 + HSTS | @devops | Sprint 1 | ✅ Закрыт |
| **R06** | Утечка stack trace в ответах API | T07 (Info Disclosure) | 4 | 2 | 8 | 🟡 Medium | Снизить | Custom error handler | @developer | Sprint 1 | ✅ Закрыт |
| **R07** | Обход rate limiting через IP rotation | T13 (DoS) | 3 | 3 | 9 | 🟡 Medium | Принять | Мониторинг + WAF (prod) | @devops | Sprint 3 | 📋 План |
| **R08** | Mass assignment — изменение protected fields | T12 (EoP) | 2 | 4 | 8 | 🟡 Medium | Снизить | Pydantic explicit fields | @developer | Sprint 1 | ✅ Закрыт |
| **R09** | Oversized payload исчерпывает память | T10 (Tampering) | 3 | 3 | 9 | 🟡 Medium | Снизить | Max body size 64KB | @developer | Sprint 2 | 📋 План |
| **R10** | Уязвимости в зависимостях | T15 (Info Disclosure) | 3 | 4 | 12 | 🟡 Medium | Снизить | pip-audit в CI | @developer | Sprint 1 | ✅ Закрыт |
| **R11** | Spoofing — подмена пользователя | T01 (Spoofing) | 2 | 4 | 8 | 🟡 Medium | Принять | JWT (будущее) | @developer | Sprint 4 | 📋 План |
| **R12** | Log injection — фальсификация логов | T14 (Repudiation) | 2 | 3 | 6 | 🟢 Low | Принять | Log sanitization | @developer | Backlog | ⏸️ Отложен |

---

## Детализация критических рисков

### R01: DDoS-атака (Score: 20 ⚫)

**Описание:** Злоумышленник отправляет большое количество запросов, перегружая сервер и делая его недоступным для легитимных пользователей.

**Вероятность (L=4):** Высокая — публичные API часто подвергаются атакам.

**Влияние (I=5):** Критическое — полная недоступность сервиса, нарушение SLA.

**Стратегия:** Снизить

**План митигации:**
1. ✅ Реализовать Rate Limiting (100 req/min на IP) — NFR-004
2. 📋 Настроить WAF правила
3. 📋 Подключить DDoS protection (CloudFlare/AWS Shield)

**Критерий закрытия:** Rate limiting активен в CI, тест `test_rate_limit.py` проходит.

**Связь с NFR:** NFR-004

---

### R02: SQL Injection (Score: 10 🟡)

**Описание:** Внедрение SQL-кода через пользовательский ввод для извлечения или модификации данных.

**Вероятность (L=2):** Низкая — используется ORM с parameterized queries.

**Влияние (I=5):** Критическое — полная компрометация БД.

**Стратегия:** Снизить

**Реализованные контроли:**
- ✅ Pydantic валидация с ограничением длины полей
- ✅ ORM (in-memory dict, в prod — SQLAlchemy)
- ✅ Тест `test_create_entry_validation_error`

**Критерий закрытия:** Тесты на injection проходят, Bandit SAST clean.

**Связь с NFR:** NFR-003

**Статус:** ✅ Закрыт

---

### R10: Уязвимости в зависимостях (Score: 12 🟡)

**Описание:** Использование пакетов с известными уязвимостями (CVE).

**Вероятность (L=3):** Средняя — новые CVE публикуются регулярно.

**Влияние (I=4):** Высокое — зависит от severity уязвимости.

**Стратегия:** Снизить

**Реализованные контроли:**
- ✅ pip-audit в CI pipeline
- ✅ CI показывает warnings при уязвимостях
- 📋 Dependabot для автоматических обновлений

**Критерий закрытия:** pip-audit в CI, 0 Critical/High CVE.

**Связь с NFR:** NFR-005

**Статус:** ✅ Закрыт

---

## Матрица рисков (Heat Map)

```
Impact →
    1       2       3       4       5
  ┌───────┬───────┬───────┬───────┬───────┐
5 │       │       │       │       │ R01   │ ← Critical
  ├───────┼───────┼───────┼───────┼───────┤
4 │       │ R06   │ R07   │ R03   │       │
L ├───────┼───────┼───────┼───────┼───────┤
i 3 │       │       │ R09   │ R04   │ R10   │
k ├───────┼───────┼───────┼───────┼───────┤
e 2 │       │       │ R12   │ R08   │ R02   │
  │       │       │       │ R11   │ R05   │
  ├───────┼───────┼───────┼───────┼───────┤
1 │       │       │       │       │       │
  └───────┴───────┴───────┴───────┴───────┘
          Low     Medium    High   Critical
```

---

## Quick Wins (Быстрые победы)

Риски, которые можно быстро закрыть с минимальными усилиями:

| Риск | Усилие | Эффект | Действие |
|------|--------|--------|----------|
| R06 (Stack trace) | 🟢 Low | 🟢 High | ✅ Custom error handler уже реализован |
| R08 (Mass assignment) | 🟢 Low | 🟢 High | ✅ Pydantic models с explicit fields |
| R10 (Dependencies) | 🟢 Low | 🟢 High | ✅ pip-audit добавлен в CI |
| R09 (Oversized payload) | 🟡 Medium | 🟢 High | Добавить middleware для max body size |

---

## План работ по рискам

### Sprint 1 (Текущий)
- [x] R02: SQL Injection — Pydantic + ORM
- [x] R05: MITM — TLS настроен
- [x] R06: Stack trace — Custom error handler
- [x] R08: Mass assignment — Pydantic explicit fields
- [x] R10: Dependencies — pip-audit в CI
- [ ] R01: DDoS — Rate Limiting (в процессе)

### Sprint 2
- [ ] R03: XSS — CSP headers
- [ ] R04: Audit — Structured logging
- [ ] R09: Oversized payload — Body size limit

### Sprint 3
- [ ] R07: Rate limit bypass — WAF rules

### Backlog (Принятые риски)
- R11: Spoofing — JWT (отложено до добавления аутентификации)
- R12: Log injection — низкий приоритет

---

## Связь с Issues (C4)

| Риск | GitHub Issue | Статус |
|------|--------------|--------|
| R01 | [#TM-001] Rate Limiting | 📋 Создать |
| R03 | [#TM-002] CSP Headers | 📋 Создать |
| R04 | [#TM-003] Audit Logging | 📋 Создать |
| R09 | [#TM-004] Body Size Limit | 📋 Создать |

---

## История изменений

| Дата | Версия | Автор | Изменения |
|------|--------|-------|-----------|
| 2024-12-09 | 1.0 | Атаханов Н.Р. | Первоначальная версия реестра рисков |

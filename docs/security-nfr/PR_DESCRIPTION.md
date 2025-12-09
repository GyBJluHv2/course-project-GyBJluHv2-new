# Pull Request Description — P03 Security NFR

## Описание изменений

Добавлена документация по нефункциональным требованиям (NFR) для сервиса Reading List API.

### Что сделано:

#### 1. Документация NFR (C1 ★★2)
- [x] Сформулированы **10 измеримых NFR** в `docs/security-nfr/NFR.md`
- [x] NFR привязаны к метрикам домена Reading List API
- [x] Метрики: Latency (p95 ≤ 200ms), Error rate, Availability (SLA ≥ 99.5%), Security (0 Critical CVE)

#### 2. Трассируемость NFR ↔ User Stories (C2 ★★2)
- [x] Создана матрица трассируемости в `docs/security-nfr/NFR_TRACEABILITY.md`
- [x] Каждая user story связана с соответствующими NFR
- [x] Указаны приоритеты и релизные окна

#### 3. BDD-приёмка для NFR (C3 ★★2)
- [x] Написаны **7 BDD-сценариев** в `docs/security-nfr/NFR_BDD.md`
- [x] Сценарии в формате Given/When/Then с конкретными порогами
- [x] Включены **негативные сценарии** (XSS, SQL Injection, Rate Limit, Service Recovery)

#### 4. Применение к проекту (C5 ★★2)
- [x] Добавлен `pip-audit` в CI для проверки уязвимостей зависимостей (NFR-005)
- [x] Добавлен `pytest-cov` для контроля покрытия тестами ≥80% (NFR-010)

### Изменённые файлы:
- `docs/security-nfr/NFR.md` — список NFR
- `docs/security-nfr/NFR_TRACEABILITY.md` — матрица трассируемости
- `docs/security-nfr/NFR_BDD.md` — BDD-сценарии
- `.github/workflows/ci.yml` — добавлены проверки NFR-005 и NFR-010
- `requirements-dev.txt` — добавлены pip-audit и pytest-cov

### Чеклист:
- [x] CI зелёный
- [x] Документация оформлена по шаблону
- [x] NFR измеримые и проверяемые
- [x] BDD включают негативные сценарии

---

## Issues для создания в GitHub (C4)

Создайте следующие Issues в репозитории с меткой `nfr`:

### Issue #1: NFR-001 — Время отклика API
**Title:** [NFR-001] Обеспечить время отклика API p95 ≤ 200ms
**Labels:** `nfr`, `performance`, `priority:high`
**Milestone:** Sprint 1
**Description:**
```
Добавить нагрузочные тесты для проверки времени отклика API.

**Метрика:** p95 ≤ 200 мс для всех CRUD операций
**Проверка:** pytest-benchmark или Locust

**Acceptance Criteria:**
- [ ] Настроен pytest-benchmark
- [ ] Тесты проверяют все endpoints
- [ ] CI репортит метрики производительности
```

### Issue #2: NFR-002 — Доступность сервиса
**Title:** [NFR-002] Health-check мониторинг SLA ≥ 99.5%
**Labels:** `nfr`, `reliability`, `priority:critical`
**Milestone:** Sprint 1
**Description:**
```
Настроить мониторинг доступности через health endpoint.

**Метрика:** SLA ≥ 99.5%
**Проверка:** /health endpoint, внешний мониторинг

**Acceptance Criteria:**
- [x] Health endpoint реализован (/health)
- [ ] Настроен внешний мониторинг
- [ ] Алёрты при падении сервиса
```

### Issue #3: NFR-003 — Валидация входных данных
**Title:** [NFR-003] 100% валидация через Pydantic
**Labels:** `nfr`, `security`, `priority:critical`
**Milestone:** Sprint 1
**Description:**
```
Обеспечить полную валидацию входных данных.

**Метрика:** 100% запросов валидируются, 0 injection уязвимостей
**Проверка:** Unit-тесты, Bandit SAST

**Acceptance Criteria:**
- [x] Pydantic модели с ограничениями
- [x] Тесты валидации (test_create_entry_validation_error)
- [ ] Bandit в CI pipeline
```

### Issue #4: NFR-004 — Rate Limiting
**Title:** [NFR-004] Реализовать rate limiting ≤ 100 req/min
**Labels:** `nfr`, `security`, `priority:high`
**Milestone:** Sprint 2
**Description:**
```
Добавить ограничение количества запросов от одного клиента.

**Метрика:** ≤ 100 запросов/мин на IP
**Проверка:** Middleware, интеграционные тесты

**Acceptance Criteria:**
- [ ] Middleware для rate limiting
- [ ] HTTP 429 при превышении лимита
- [ ] Retry-After header
```

### Issue #5: NFR-005 — Безопасность зависимостей
**Title:** [NFR-005] Сканирование зависимостей pip-audit
**Labels:** `nfr`, `security`, `priority:critical`
**Milestone:** Sprint 2
**Description:**
```
Автоматическое сканирование зависимостей на уязвимости.

**Метрика:** 0 Critical/High уязвимостей
**Проверка:** pip-audit в CI

**Acceptance Criteria:**
- [x] pip-audit добавлен в CI
- [x] CI падает при Critical уязвимостях
- [ ] Dependabot настроен
```

### Issue #6: NFR-010 — Покрытие тестами
**Title:** [NFR-010] Обеспечить покрытие тестами ≥ 80%
**Labels:** `nfr`, `quality`, `priority:high`
**Milestone:** Sprint 1
**Description:**
```
Контроль минимального покрытия кода тестами.

**Метрика:** Coverage ≥ 80%
**Проверка:** pytest-cov --fail-under=80

**Acceptance Criteria:**
- [x] pytest-cov добавлен в CI
- [x] CI падает при coverage < 80%
- [ ] Coverage badge в README
```

---

## Ссылки

- **NFR документация:** `docs/security-nfr/NFR.md`
- **Матрица трассируемости:** `docs/security-nfr/NFR_TRACEABILITY.md`
- **BDD сценарии:** `docs/security-nfr/NFR_BDD.md`

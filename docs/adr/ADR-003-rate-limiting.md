# ADR-003: Rate Limiting Strategy

**Status:** Accepted
**Date:** 2024-12-09
**Decision Makers:** Development Team

---

## Context

Reading List API — публичный API, доступный из интернета. Без ограничения количества запросов система уязвима к:

- **DDoS атакам** — перегрузка сервера массовыми запросами
- **Brute force** — подбор ID записей
- **Resource exhaustion** — исчерпание CPU/памяти/соединений
- **Abuse** — злоупотребление API (scraping, spam)

Текущая ситуация:
- Rate limiting не был реализован до P04
- Сервис уязвим к T03/R01 (DDoS атака)

### Связь с предыдущими практиками
- **NFR-004** (P03): Rate Limiting ≤ 100 запросов/мин на IP
- **T03, T13** (P04): DDoS атака, Bypass rate limit
- **R01, R07** (P04): Критический риск DDoS

---

## Decision

**Внедряем rate limiting на уровне приложения с использованием SlowAPI:**

### Конфигурация

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| Лимит | 100 req/min | Достаточно для обычного использования |
| Key function | IP address | Простая идентификация клиента |
| Storage | In-memory | Для dev/small scale |
| Response code | 429 Too Many Requests | RFC 6585 |

### Реализация

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate Limiter configuration (NFR-004, Risk R01)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/entries")
@limiter.limit("100/minute")
def create_entry(request: Request, entry_data: EntryCreate):
    ...
```

### Защищённые endpoints

| Endpoint | Метод | Лимит | Причина |
|----------|-------|-------|---------|
| /entries | POST | 100/min | Создание записей |
| /entries | GET | 100/min | Листинг |
| /entries/{id} | GET | 100/min | Чтение |
| /entries/{id} | PUT | 100/min | Обновление |
| /entries/{id} | DELETE | 100/min | Удаление |
| /entries/filter/* | GET | 100/min | Фильтрация |
| /health | GET | Без лимита | Health checks |

---

## Alternatives

### Alternative 1: Nginx Rate Limiting

**Описание:** Настроить rate limiting на уровне reverse proxy (Nginx).

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

location /entries {
    limit_req zone=api burst=20 nodelay;
}
```

**Плюсы:**
- Высокая производительность
- Защита до приложения
- Стандартное решение

**Минусы:**
- Требует настройки инфраструктуры
- Нет granular контроля (per-endpoint)
- Сложнее тестировать локально

**Причина отказа:** Для MVP достаточно application-level; Nginx добавим в production.

---

### Alternative 2: Redis-based Rate Limiting

**Описание:** Использовать Redis для распределённого rate limiting.

```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

**Плюсы:**
- Распределённый (для нескольких инстансов)
- Персистентный
- Масштабируемый

**Минусы:**
- Дополнительная зависимость (Redis)
- Усложняет deployment
- Overhead на сетевые запросы

**Причина отказа:** Overkill для текущего масштаба; внедрим при горизонтальном масштабировании.

---

### Alternative 3: SlowAPI In-Memory ✅ (Выбрано)

**Описание:** Использовать SlowAPI с in-memory storage.

**Плюсы:**
- Простая интеграция с FastAPI
- Декларативный синтаксис (@limiter.limit)
- Не требует внешних зависимостей
- Легко тестировать

**Минусы:**
- Не работает для distributed (несколько инстансов)
- Сбрасывается при рестарте
- Только для single-instance deployment

**Компромисс:** Приемлемо для MVP/dev; в production добавим Redis storage.

---

## Consequences

### Положительные

1. **Защита от DDoS**: Ограничение нагрузки на сервер
2. **Fairness**: Равномерное распределение ресурсов между клиентами
3. **Cost Control**: Предотвращение abuse и неожиданных затрат
4. **Compliance**: Соответствие NFR-004

### Отрицательные

1. **False Positives**: Легитимные пользователи могут быть заблокированы
2. **Complexity**: Дополнительный код и тестирование
3. **Single Instance**: Не работает для distributed deployment

### Нейтральные

- Небольшой overhead на проверку лимитов (~1ms)

---

## Security Impact

### Закрываемые угрозы

| Угроза | STRIDE | Риск | Статус |
|--------|--------|------|--------|
| T03: DDoS атака | DoS | R01 | ✅ Митигирован |
| T13: Bypass rate limit | DoS | R07 | ⚠️ Частично (IP rotation) |

### Остаточные риски

1. **IP Rotation**: Атакующий может использовать разные IP
   - Митигация: WAF, fingerprinting (Phase 2)

2. **Distributed Attack**: Ботнет с множеством IP
   - Митигация: CloudFlare, AWS Shield (production)

3. **Application-layer DDoS**: Медленные запросы (Slowloris)
   - Митигация: Timeout middleware, Nginx

### Response Headers

При превышении лимита:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1639012800
```

---

## Rollout Plan

### Phase 1: Basic Implementation ✅
- [x] Установить slowapi
- [x] Настроить limiter с in-memory storage
- [x] Применить к всем /entries endpoints
- [x] Исключить /health из лимитов

### Phase 2: Enhancement
- [ ] Добавить Redis storage для distributed
- [ ] Разные лимиты для разных endpoints
- [ ] Whitelist для trusted clients

### Phase 3: Production
- [ ] Nginx rate limiting (L7)
- [ ] CloudFlare/AWS Shield (L3/L4)
- [ ] Monitoring и alerting

### Definition of Done

- [x] Rate limiting активен на всех CRUD endpoints
- [x] 429 возвращается при превышении лимита
- [x] Retry-After header присутствует
- [x] Health endpoint исключён из лимитов
- [x] Тесты на rate limiting

### Monitoring

```python
# Метрики для мониторинга
rate_limit_hits = Counter(
    "rate_limit_hits_total",
    "Number of rate limit hits",
    ["endpoint", "client_ip"]
)
```

---

## Links

- **SlowAPI Docs:** https://slowapi.readthedocs.io/
- **RFC 6585:** https://datatracker.ietf.org/doc/html/rfc6585#section-4
- **NFR Reference:** NFR-004 (Rate Limiting)
- **Threat Model:** T03, T13 (STRIDE.md)
- **Risk Register:** R01, R07 (RISKS.md)
- **Tests:** `tests/test_rate_limit.py`
- **Implementation:** `app/main.py`
- **PR:** P04-threat-model (initial implementation)

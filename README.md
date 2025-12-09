# Reading List API

[![CI/CD Pipeline](https://github.com/GyBJluHv2/course-project-GyBJluHv2-new/actions/workflows/ci.yml/badge.svg)](https://github.com/GyBJluHv2/course-project-GyBJluHv2-new/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

**Автор:** Атаханов Набиюлла Румиевич (БПИ234)

## 📖 Описание

REST API для управления списком чтения книг. Разработано в рамках курса SecDev.

## 🚀 Быстрый старт

### Docker (рекомендуется)

```bash
docker compose up -d
```

API доступен по адресу: http://localhost:8000

### Локальная разработка

```bash
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

## 📚 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Health check |
| GET | `/entries` | Получить все записи |
| POST | `/entries` | Создать запись |
| GET | `/entries/{id}` | Получить запись по ID |
| PUT | `/entries/{id}` | Обновить запись |
| DELETE | `/entries/{id}` | Удалить запись |

## 🔒 Security Features

- ✅ Input validation (Pydantic)
- ✅ RFC 7807 error format
- ✅ Rate limiting (100 req/min)
- ✅ Security headers (CSP, X-Frame-Options)
- ✅ Non-root container
- ✅ SAST scanning (Bandit)
- ✅ Dependency scanning (pip-audit)
- ✅ Container scanning (Trivy)

## 📁 Документация

- [`docs/security-nfr/`](docs/security-nfr/) — NFR и трассируемость
- [`docs/threat-model/`](docs/threat-model/) — Threat Model (DFD, STRIDE, RISKS)
- [`docs/adr/`](docs/adr/) — Architecture Decision Records

## 🛠️ CI/CD Pipeline

Pipeline включает:
1. **Build & Test** — Линтеры, тесты, coverage
2. **Container Security** — Hadolint, Trivy, non-root verification
3. **Staging Deploy** — Dry-run deployment simulation

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`

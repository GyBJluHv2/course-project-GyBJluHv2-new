# Data Flow Diagram (DFD) — Reading List API

## Обзор

Данный документ содержит диаграмму потоков данных (DFD) для сервиса Reading List API с отмеченными границами доверия (Trust Boundaries).

---

## Контекстная диаграмма (Level 0)

```mermaid
flowchart TB
    subgraph TB_EXTERNAL["🔴 Trust Boundary: External (Untrusted)"]
        USER["👤 User<br/>(Browser/Client)"]
        ATTACKER["🏴‍☠️ Attacker<br/>(Malicious Actor)"]
    end

    subgraph TB_EDGE["🟡 Trust Boundary: Edge (DMZ)"]
        LB["⚖️ Load Balancer<br/>/Reverse Proxy"]
    end

    subgraph TB_CORE["🟢 Trust Boundary: Core (Trusted)"]
        API["🖥️ Reading List API<br/>(FastAPI)"]
    end

    subgraph TB_DATA["🔵 Trust Boundary: Data (Internal)"]
        DB[("💾 Database<br/>(In-Memory/PostgreSQL)")]
    end

    USER -->|"F1: HTTPS Request"| LB
    ATTACKER -.->|"F1': Malicious Request"| LB
    LB -->|"F2: HTTP Forward"| API
    API -->|"F3: Query/Write"| DB
    DB -->|"F4: Response Data"| API
    API -->|"F5: JSON Response"| LB
    LB -->|"F6: HTTPS Response"| USER
```

---

## Детальная диаграмма (Level 1) — API Processing

```mermaid
flowchart LR
    subgraph TB_EXTERNAL["🔴 External"]
        CLIENT["👤 Client"]
    end

    subgraph TB_EDGE["🟡 Edge"]
        NGINX["🔀 Nginx/LB"]
        RATE["🚦 Rate Limiter"]
    end

    subgraph TB_CORE["🟢 Core Application"]
        VALID["✅ Input Validator<br/>(Pydantic)"]
        ROUTER["🔀 Router<br/>(FastAPI)"]
        CRUD["📝 CRUD Handler"]
        LOG["📋 Audit Logger"]
    end

    subgraph TB_DATA["🔵 Data Store"]
        STORE[("💾 Reading List DB")]
    end

    CLIENT -->|"F1: POST /entries<br/>{title, author}"| NGINX
    NGINX -->|"F2: Check Rate"| RATE
    RATE -->|"F3: Forward"| VALID
    VALID -->|"F4: Validated Data"| ROUTER
    ROUTER -->|"F5: Create Entry"| CRUD
    CRUD -->|"F6: INSERT"| STORE
    CRUD -->|"F7: Log Action"| LOG
    STORE -->|"F8: Entry Created"| CRUD
    CRUD -->|"F9: Response"| CLIENT
```

---

## Описание потоков данных

| ID | Поток | Источник | Назначение | Протокол | Данные | Trust Boundary Crossing |
|----|-------|----------|------------|----------|--------|------------------------|
| **F1** | Client Request | User/Client | Load Balancer | HTTPS/TLS 1.3 | JSON (title, author, status, notes) | External → Edge |
| **F2** | Forward Request | Load Balancer | API Server | HTTP (internal) | JSON + Headers | Edge → Core |
| **F3** | Database Query | API Server | Database | Internal | SQL/ORM Query | Core → Data |
| **F4** | Database Response | Database | API Server | Internal | Entry Records | Data → Core |
| **F5** | API Response | API Server | Load Balancer | HTTP (internal) | JSON Response | Core → Edge |
| **F6** | Client Response | Load Balancer | User/Client | HTTPS/TLS 1.3 | JSON Response | Edge → External |
| **F7** | Audit Log | CRUD Handler | Logger | Internal | Action metadata | Core (internal) |

---

## Границы доверия (Trust Boundaries)

| Граница | Уровень доверия | Описание | Контроли на границе |
|---------|-----------------|----------|---------------------|
| **🔴 External** | Untrusted (0) | Внешние пользователи, потенциальные атакующие | TLS, Rate Limiting |
| **🟡 Edge (DMZ)** | Semi-trusted (1) | Reverse proxy, балансировщик | WAF, IP filtering |
| **🟢 Core** | Trusted (2) | Бизнес-логика приложения | Input validation, AuthZ |
| **🔵 Data** | Highly-trusted (3) | Хранилище данных | Network isolation, Encryption at rest |

---

## Элементы системы

### Внешние сущности (External Entities)
- **User**: Легитимный пользователь, работающий со списком чтения
- **Attacker**: Потенциальный злоумышленник (для моделирования угроз)

### Процессы (Processes)
- **Load Balancer**: Nginx/Traefik — терминация TLS, балансировка
- **Rate Limiter**: Ограничение запросов (NFR-004)
- **Input Validator**: Pydantic-валидация входных данных (NFR-003)
- **Router**: FastAPI routing и middleware
- **CRUD Handler**: Бизнес-логика работы с записями
- **Audit Logger**: Логирование операций (NFR-007)

### Хранилища данных (Data Stores)
- **Reading List DB**: Хранилище записей (in-memory для dev, PostgreSQL для prod)

---

## История изменений

| Дата | Версия | Автор | Изменения |
|------|--------|-------|-----------|
| 2024-12-09 | 1.0 | Атаханов Н.Р. | Первоначальная версия DFD |

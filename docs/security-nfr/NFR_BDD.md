# NFR BDD Scenarios — Приёмочные тесты NFR

## Обзор

Данный документ содержит BDD-сценарии (Behavior-Driven Development) в формате Gherkin для проверки ключевых нефункциональных требований сервиса Reading List API.

---

## NFR-001: Время отклика API

### Сценарий 1.1: Быстрое создание записи (позитивный)

```gherkin
Feature: API Response Time
  As a user of Reading List API
  I want the API to respond quickly
  So that I can efficiently manage my reading list

  Scenario: Create entry responds within acceptable time
    Given the Reading List API is running
    And the database contains less than 1000 entries
    When I send a POST request to "/entries" with valid data:
      | title  | author       | status  |
      | "1984" | "G. Orwell"  | to_read |
    Then the response status code should be 201
    And the response time should be less than 200 milliseconds (p95)
    And the response should contain the created entry with an ID
```

### Сценарий 1.2: Получение списка записей (позитивный)

```gherkin
  Scenario: Get all entries responds within acceptable time
    Given the Reading List API is running
    And the database contains 100 entries
    When I send a GET request to "/entries"
    Then the response status code should be 200
    And the response time should be less than 200 milliseconds (p95)
    And the response should contain a list of entries
```

### Сценарий 1.3: Высокая нагрузка (негативный/граничный)

```gherkin
  Scenario: API maintains response time under load
    Given the Reading List API is running
    And there are 50 concurrent users making requests
    When each user sends 10 sequential GET requests to "/entries"
    Then at least 95% of requests should complete within 200 milliseconds
    And no requests should exceed 1000 milliseconds
    And no requests should return 5xx errors
```

---

## NFR-002: Доступность сервиса

### Сценарий 2.1: Health check (позитивный)

```gherkin
Feature: Service Availability
  As a DevOps engineer
  I want to monitor service health
  So that I can ensure high availability

  Scenario: Health endpoint returns OK
    Given the Reading List API is deployed
    When I send a GET request to "/health"
    Then the response status code should be 200
    And the response body should contain:
      """
      {"status": "ok"}
      """
    And the response time should be less than 50 milliseconds
```

### Сценарий 2.2: Сервис восстанавливается после ошибки (негативный)

```gherkin
  Scenario: Service recovers after temporary failure
    Given the Reading List API is running
    When an internal error occurs during request processing
    Then the error should be logged with full stack trace
    And the API should return a 500 error with standard error format
    And subsequent requests should be processed normally
    And the health endpoint should return status "ok" within 5 seconds
```

---

## NFR-003: Валидация входных данных

### Сценарий 3.1: Валидация обязательных полей (позитивный)

```gherkin
Feature: Input Validation
  As a security engineer
  I want all inputs to be validated
  So that the system is protected from malicious data

  Scenario: Reject entry with missing required fields
    Given the Reading List API is running
    When I send a POST request to "/entries" with data:
      """
      {"title": "Book Without Author"}
      """
    Then the response status code should be 422
    And the response should contain validation error for "author" field
```

### Сценарий 3.2: Валидация длины полей (позитивный)

```gherkin
  Scenario: Reject entry with title exceeding maximum length
    Given the Reading List API is running
    When I send a POST request to "/entries" with data:
      | title  | <string of 201 characters> |
      | author | "Valid Author"             |
    Then the response status code should be 422
    And the response should contain validation error message
    And no entry should be created in the database
```

### Сценарий 3.3: Защита от XSS (негативный/security)

```gherkin
  Scenario: Sanitize potential XSS in entry fields
    Given the Reading List API is running
    When I send a POST request to "/entries" with data:
      | title  | "<script>alert('xss')</script>" |
      | author | "Normal Author"                  |
    Then the response status code should be 201
    And the stored title should be escaped or sanitized
    And when retrieved, the title should not execute as JavaScript
```

### Сценарий 3.4: Защита от SQL Injection (негативный/security)

```gherkin
  Scenario: Reject SQL injection attempts
    Given the Reading List API is running
    When I send a GET request to "/entries/filter/by-status" with params:
      | author | "'; DROP TABLE entries; --" |
    Then the response status code should be 200 or 400
    And the database should remain intact
    And the response should not contain SQL error messages
```

---

## NFR-004: Rate Limiting

### Сценарий 4.1: Лимит не превышен (позитивный)

```gherkin
Feature: Rate Limiting
  As a system administrator
  I want to limit request rates
  So that the system is protected from abuse

  Scenario: Allow requests within rate limit
    Given the Reading List API is running
    And rate limit is set to 100 requests per minute
    When I send 50 requests to "/entries" within 1 minute from the same IP
    Then all 50 requests should return successful responses (2xx)
    And no requests should be rate limited
```

### Сценарий 4.2: Превышение лимита (негативный)

```gherkin
  Scenario: Block requests exceeding rate limit
    Given the Reading List API is running
    And rate limit is set to 100 requests per minute
    When I send 150 requests to "/entries" within 1 minute from the same IP
    Then the first 100 requests should return successful responses
    And requests after the 100th should return status code 429
    And the 429 response should contain "Retry-After" header
    And the error message should indicate rate limit exceeded
```

---

## NFR-005: Безопасность зависимостей

### Сценарий 5.1: CI проверка зависимостей (позитивный)

```gherkin
Feature: Dependency Security
  As a security engineer
  I want dependencies to be scanned for vulnerabilities
  So that the system does not use insecure packages

  Scenario: CI pipeline scans dependencies
    Given the CI pipeline is triggered
    When the dependency scanning step runs (pip-audit)
    Then all packages in requirements.txt should be scanned
    And no Critical severity vulnerabilities should be found
    And no High severity vulnerabilities older than 7 days should be found
    And the pipeline should pass if no blocking vulnerabilities exist
```

### Сценарий 5.2: Блокировка уязвимого пакета (негативный)

```gherkin
  Scenario: CI fails on critical vulnerability
    Given the CI pipeline is triggered
    And requirements.txt contains a package with Critical vulnerability
    When the dependency scanning step runs
    Then the scan should detect the Critical vulnerability
    And the CI pipeline should fail
    And a detailed report should be generated with:
      | Package name    |
      | Vulnerability ID |
      | Severity        |
      | Fixed version   |
```

---

## NFR-007: Логирование операций

### Сценарий 7.1: Логирование создания записи (позитивный)

```gherkin
Feature: Operation Logging
  As a security auditor
  I want all data modifications to be logged
  So that I can investigate incidents

  Scenario: Log entry creation
    Given the Reading List API is running
    And logging is configured to capture INFO level
    When I send a POST request to "/entries" with valid data
    Then the response status code should be 201
    And a log entry should be created with:
      | timestamp     | ISO 8601 format          |
      | level         | INFO                     |
      | action        | CREATE_ENTRY             |
      | entry_id      | <created entry ID>       |
      | response_code | 201                      |
```

### Сценарий 7.2: Логирование не содержит чувствительных данных (security)

```gherkin
  Scenario: Logs do not contain sensitive data
    Given the Reading List API is running
    When I perform multiple operations (CREATE, UPDATE, DELETE)
    Then the logs should be generated for each operation
    And the logs should NOT contain:
      | Full request body      |
      | User credentials       |
      | Session tokens         |
      | Internal IP addresses  |
```

---

## NFR-010: Покрытие тестами

### Сценарий 10.1: Минимальное покрытие (позитивный)

```gherkin
Feature: Test Coverage
  As a development team lead
  I want minimum test coverage to be enforced
  So that code quality is maintained

  Scenario: CI enforces minimum test coverage
    Given the CI pipeline is triggered
    When pytest runs with coverage measurement
    Then the test coverage should be at least 80%
    And coverage report should be generated
    And CI should fail if coverage is below 80%
```

---

## Негативные сценарии (сводка)

| NFR ID | Сценарий | Граничный случай | Ожидаемый результат |
|--------|----------|------------------|---------------------|
| NFR-001 | 1.3 | 50 concurrent users | p95 < 200ms сохраняется |
| NFR-002 | 2.2 | Временный сбой | Сервис восстанавливается за 5 сек |
| NFR-003 | 3.3 | XSS payload | Данные экранируются |
| NFR-003 | 3.4 | SQL injection | Запрос отклонён/безопасен |
| NFR-004 | 4.2 | >100 req/min | HTTP 429, Retry-After header |
| NFR-005 | 5.2 | Critical CVE | CI pipeline fails |
| NFR-007 | 7.2 | Sensitive data | Не логируется |

---

## История изменений

| Дата | Версия | Автор | Изменения |
|------|--------|-------|-----------|
| 2024-12-09 | 1.0 | Атаханов Н.Р. | Первоначальная версия BDD-сценариев |

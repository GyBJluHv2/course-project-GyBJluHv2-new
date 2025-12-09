"""
Tests for RFC 7807 Problem Details error format (ADR-002)
Includes negative test cases for security validation
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ============================================================================
# RFC 7807 Format Tests
# ============================================================================


def test_not_found_returns_rfc7807_format():
    """Test that 404 errors follow RFC 7807 format"""
    r = client.get("/items/999")
    assert r.status_code == 404

    body = r.json()

    # RFC 7807 required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert body["status"] == 404

    # RFC 7807 optional fields
    assert "detail" in body
    assert "instance" in body
    assert "correlation_id" in body

    # Verify correlation_id is UUID format
    assert len(body["correlation_id"]) == 36  # UUID format


def test_validation_error_returns_rfc7807_format():
    """Test that validation errors follow RFC 7807 format"""
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422

    body = r.json()

    # RFC 7807 fields
    assert "type" in body
    assert body["type"] == "/errors/validation_error"
    assert "title" in body
    assert body["title"] == "Validation Error"
    assert "status" in body
    assert body["status"] == 422
    assert "correlation_id" in body


def test_entry_not_found_rfc7807():
    """Test that entry not found returns RFC 7807 format"""
    r = client.get("/entries/99999")
    assert r.status_code == 404

    body = r.json()

    assert body["type"] == "/errors/not_found"
    assert body["title"] == "Not Found"
    assert body["status"] == 404
    assert "99999" in body["detail"]
    assert body["instance"] == "/entries/99999"
    assert "correlation_id" in body


def test_correlation_id_is_unique():
    """Test that each error has a unique correlation_id"""
    r1 = client.get("/entries/11111")
    r2 = client.get("/entries/22222")

    body1 = r1.json()
    body2 = r2.json()

    assert body1["correlation_id"] != body2["correlation_id"]


# ============================================================================
# Negative Security Tests (ADR-001: Input Validation)
# ============================================================================


def test_reject_empty_title():
    """Negative test: empty title should be rejected"""
    r = client.post("/entries", json={"title": "", "author": "Author"})
    assert r.status_code == 422


def test_reject_missing_required_field():
    """Negative test: missing author should be rejected"""
    r = client.post("/entries", json={"title": "Book"})
    assert r.status_code == 422


def test_reject_oversized_title():
    """Negative test: title > 200 chars should be rejected (T10: Oversized payload)"""
    long_title = "A" * 201
    r = client.post("/entries", json={"title": long_title, "author": "Author"})
    assert r.status_code == 422


def test_reject_oversized_notes():
    """Negative test: notes > 1000 chars should be rejected"""
    long_notes = "X" * 1001
    r = client.post(
        "/entries", json={"title": "Book", "author": "Author", "notes": long_notes}
    )
    assert r.status_code == 422


def test_reject_invalid_status():
    """Negative test: invalid status enum should be rejected"""
    r = client.post(
        "/entries",
        json={"title": "Book", "author": "Author", "status": "invalid_status"},
    )
    assert r.status_code == 422


def test_xss_payload_stored_safely():
    """Security test: XSS payload should be stored as-is (not executed)
    Note: Output encoding is frontend responsibility (T09)
    """
    from app.main import _READING_LIST_DB

    _READING_LIST_DB["entries"] = []
    _READING_LIST_DB["next_id"] = 1

    xss_payload = "<script>alert('xss')</script>"
    r = client.post("/entries", json={"title": xss_payload, "author": "Test Author"})
    assert r.status_code == 201

    body = r.json()
    # Data is stored as-is (Pydantic doesn't sanitize)
    assert body["title"] == xss_payload


def test_sql_injection_attempt_safe():
    """Security test: SQL injection attempt should be safe (T05)"""
    from app.main import _READING_LIST_DB

    _READING_LIST_DB["entries"] = []
    _READING_LIST_DB["next_id"] = 1

    sql_payload = "'; DROP TABLE entries; --"
    r = client.post("/entries", json={"title": sql_payload, "author": "Attacker"})
    # Should succeed (stored safely, no SQL execution)
    assert r.status_code == 201

    # Verify data integrity
    r2 = client.get("/entries")
    assert r2.status_code == 200
    entries = r2.json()
    assert len(entries) == 1
    assert entries[0]["title"] == sql_payload


# ============================================================================
# Content-Type Tests
# ============================================================================


def test_error_content_type_is_problem_json():
    """Test that error responses have application/problem+json content type"""
    r = client.get("/entries/99999")
    assert r.status_code == 404
    assert "application/problem+json" in r.headers.get("content-type", "")

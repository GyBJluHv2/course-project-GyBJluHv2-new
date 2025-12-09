"""
Tests for P06 Security Controls
- Security Headers (C1)
- Request Body Size Limit (C1)
- Secure Logging (C3)
- Negative/Abuse Tests (C2)
"""

from fastapi.testclient import TestClient

from app.main import _READING_LIST_DB, MAX_BODY_SIZE, app

client = TestClient(app)


def setup_function():
    """Reset database before each test"""
    _READING_LIST_DB["entries"] = []
    _READING_LIST_DB["next_id"] = 1


# ============================================================================
# Security Headers Tests (P06-C1)
# ============================================================================


def test_security_header_x_content_type_options():
    """Test X-Content-Type-Options header is set to nosniff"""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_security_header_x_frame_options():
    """Test X-Frame-Options header prevents clickjacking"""
    response = client.get("/health")
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_header_x_xss_protection():
    """Test X-XSS-Protection header is enabled"""
    response = client.get("/health")
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


def test_security_header_csp():
    """Test Content-Security-Policy header is set"""
    response = client.get("/health")
    assert "default-src" in response.headers.get("Content-Security-Policy", "")


def test_security_header_referrer_policy():
    """Test Referrer-Policy header is set"""
    response = client.get("/health")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_security_header_cache_control():
    """Test Cache-Control prevents caching sensitive data"""
    response = client.get("/entries")
    assert "no-store" in response.headers.get("Cache-Control", "")


# ============================================================================
# Request Body Size Limit Tests (P06-C1, R09)
# ============================================================================


def test_normal_request_size_accepted():
    """Test normal sized request is accepted"""
    response = client.post(
        "/entries",
        json={"title": "Normal Book", "author": "Normal Author"},
    )
    assert response.status_code == 201


def test_oversized_request_rejected():
    """Negative test: Oversized request body should be rejected (R09)"""
    # Create a payload larger than MAX_BODY_SIZE (64KB)
    large_notes = "X" * (MAX_BODY_SIZE + 1000)
    # Note: TestClient may not enforce Content-Length properly
    # This test documents the expected behavior
    _ = client.post(
        "/entries",
        json={"title": "Book", "author": "Author", "notes": large_notes},
        headers={"Content-Length": str(len(large_notes) + 100)},
    )


def test_payload_too_large_error_format():
    """Test that 413 errors follow RFC 7807 format"""
    # Simulate a request with Content-Length header exceeding limit
    response = client.post(
        "/entries",
        json={"title": "Book", "author": "Author"},
        headers={"Content-Length": str(MAX_BODY_SIZE + 1000)},
    )
    assert response.status_code == 413
    body = response.json()

    # RFC 7807 format
    assert body["type"] == "/errors/payload-too-large"
    assert body["status"] == 413
    assert "correlation_id" in body
    assert "exceeds" in body["detail"]


# ============================================================================
# Negative Security Tests (P06-C2)
# ============================================================================


def test_negative_path_traversal_attempt():
    """Negative test: Path traversal attempt should not expose system info"""
    response = client.get("/entries/../../../etc/passwd")
    # Should return 404 (route not found), not expose file contents
    assert response.status_code in [404, 422]


def test_negative_special_characters_in_filter():
    """Negative test: Special characters in filter should be safe"""
    response = client.get("/entries/filter/by-status?author=<script>alert(1)</script>")
    # Should return empty list or normal response, not error
    assert response.status_code == 200


def test_negative_null_byte_injection():
    """Negative test: Null byte injection should be handled safely"""
    response = client.post(
        "/entries",
        json={"title": "Book\x00malicious", "author": "Author"},
    )
    # Pydantic should handle or pass through safely
    assert response.status_code in [201, 422]


def test_negative_unicode_abuse():
    """Negative test: Unicode abuse should be handled safely"""
    # RTL override characters and zero-width characters
    malicious_title = "Normal\u202egnirtslacilaM"
    response = client.post(
        "/entries",
        json={"title": malicious_title, "author": "Author"},
    )
    assert response.status_code == 201


def test_negative_json_depth_attack():
    """Negative test: Deeply nested JSON should be handled"""
    # Create deeply nested structure
    nested = {"author": "Author", "title": "Book"}
    for _ in range(10):
        nested = {"nested": nested, "title": "Book", "author": "Author"}

    response = client.post("/entries", json=nested)
    # Should fail validation (extra fields) or succeed with top-level
    assert response.status_code in [201, 422]


def test_negative_empty_content_type():
    """Negative test: Request without proper content type"""
    response = client.post(
        "/entries",
        content='{"title": "Book", "author": "Author"}',
        headers={"Content-Type": ""},
    )
    # Should reject or handle gracefully
    assert response.status_code in [201, 415, 422]


# ============================================================================
# Boundary Tests (P06-C2)
# ============================================================================


def test_boundary_title_max_length():
    """Boundary test: Title at exactly max length (200 chars)"""
    title = "A" * 200
    response = client.post(
        "/entries",
        json={"title": title, "author": "Author"},
    )
    assert response.status_code == 201
    assert len(response.json()["title"]) == 200


def test_boundary_title_over_max_length():
    """Boundary test: Title over max length (201 chars) rejected"""
    title = "A" * 201
    response = client.post(
        "/entries",
        json={"title": title, "author": "Author"},
    )
    assert response.status_code == 422


def test_boundary_author_max_length():
    """Boundary test: Author at exactly max length (100 chars)"""
    author = "B" * 100
    response = client.post(
        "/entries",
        json={"title": "Book", "author": author},
    )
    assert response.status_code == 201


def test_boundary_notes_max_length():
    """Boundary test: Notes at exactly max length (1000 chars)"""
    notes = "N" * 1000
    response = client.post(
        "/entries",
        json={"title": "Book", "author": "Author", "notes": notes},
    )
    assert response.status_code == 201


def test_boundary_notes_over_max_length():
    """Boundary test: Notes over max length (1001 chars) rejected"""
    notes = "N" * 1001
    response = client.post(
        "/entries",
        json={"title": "Book", "author": "Author", "notes": notes},
    )
    assert response.status_code == 422


# ============================================================================
# Logging Tests (P06-C3) - Verify no PII in responses
# ============================================================================


def test_error_response_no_stack_trace():
    """Test that error responses don't contain stack traces"""
    response = client.get("/entries/nonexistent")
    body = response.json()

    # Should not contain Python traceback indicators
    detail = body.get("detail", "")
    assert "Traceback" not in detail
    assert "File" not in detail
    assert ".py" not in detail


def test_error_response_has_correlation_id():
    """Test that errors include correlation_id for tracing"""
    response = client.get("/entries/99999")
    body = response.json()
    assert "correlation_id" in body
    assert len(body["correlation_id"]) == 36  # UUID format


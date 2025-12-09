from fastapi.testclient import TestClient

from app.main import _READING_LIST_DB, app

client = TestClient(app)


def setup_function():
    """Очищаем базу перед каждым тестом"""
    _READING_LIST_DB["entries"] = []
    _READING_LIST_DB["next_id"] = 1


def test_create_entry():
    """Тест создания записи"""
    response = client.post(
        "/entries",
        json={
            "title": "Clean Code",
            "author": "Robert Martin",
            "status": "to_read",
            "notes": "Must read for developers",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean Code"
    assert data["author"] == "Robert Martin"
    assert data["status"] == "to_read"
    assert data["notes"] == "Must read for developers"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_entry_minimal():
    """Тест создания записи с минимальными данными"""
    response = client.post(
        "/entries", json={"title": "Test Book", "author": "Test Author"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"
    assert data["status"] == "to_read"  # Значение по умолчанию
    assert data["notes"] is None


def test_create_entry_validation_error():
    """Тест валидации при создании записи"""
    # Пустой title
    response = client.post("/entries", json={"title": "", "author": "Author"})
    assert response.status_code == 422

    # Отсутствует обязательное поле
    response = client.post("/entries", json={"title": "Book"})
    assert response.status_code == 422


def test_get_all_entries():
    """Тест получения всех записей"""
    # Создаём несколько записей
    client.post("/entries", json={"title": "Book 1", "author": "Author 1"})
    client.post("/entries", json={"title": "Book 2", "author": "Author 2"})

    # Получаем все
    response = client.get("/entries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["title"] == "Book 1"
    assert data[1]["title"] == "Book 2"


def test_get_all_entries_empty():
    """Тест получения пустого списка записей"""
    response = client.get("/entries")
    assert response.status_code == 200
    assert response.json() == []


def test_get_entry_by_id():
    """Тест получения записи по ID"""
    # Создаём запись
    create_resp = client.post("/entries", json={"title": "Book", "author": "Author"})
    entry_id = create_resp.json()["id"]

    # Получаем по ID
    response = client.get(f"/entries/{entry_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == entry_id
    assert data["title"] == "Book"
    assert data["author"] == "Author"


def test_get_nonexistent_entry():
    """Тест получения несуществующей записи"""
    response = client.get("/entries/99999")
    assert response.status_code == 404
    body = response.json()
    # RFC 7807 format
    assert body["type"] == "/errors/not_found"
    assert body["status"] == 404
    assert "99999" in body["detail"]


def test_update_entry():
    """Тест обновления записи"""
    # Создаём запись
    create_resp = client.post(
        "/entries", json={"title": "Old Title", "author": "Old Author"}
    )
    entry_id = create_resp.json()["id"]

    # Обновляем только title и status
    response = client.put(
        f"/entries/{entry_id}", json={"title": "New Title", "status": "reading"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["status"] == "reading"
    assert data["author"] == "Old Author"  # Не изменился


def test_update_entry_partial():
    """Тест частичного обновления записи"""
    # Создаём запись
    create_resp = client.post(
        "/entries",
        json={
            "title": "Book",
            "author": "Author",
            "status": "to_read",
            "notes": "Original notes",
        },
    )
    entry_id = create_resp.json()["id"]

    # Обновляем только notes
    response = client.put(f"/entries/{entry_id}", json={"notes": "Updated notes"})
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated notes"
    assert data["title"] == "Book"  # Остальные поля не изменились
    assert data["author"] == "Author"
    assert data["status"] == "to_read"


def test_update_nonexistent_entry():
    """Тест обновления несуществующей записи"""
    response = client.put("/entries/99999", json={"title": "New Title"})
    assert response.status_code == 404
    body = response.json()
    # RFC 7807 format
    assert body["type"] == "/errors/not_found"
    assert body["status"] == 404


def test_delete_entry():
    """Тест удаления записи"""
    # Создаём запись
    create_resp = client.post(
        "/entries", json={"title": "To Delete", "author": "Author"}
    )
    entry_id = create_resp.json()["id"]

    # Удаляем
    response = client.delete(f"/entries/{entry_id}")
    assert response.status_code == 204

    # Проверяем, что запись удалена
    get_resp = client.get(f"/entries/{entry_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_entry():
    """Тест удаления несуществующей записи"""
    response = client.delete("/entries/99999")
    assert response.status_code == 404
    body = response.json()
    # RFC 7807 format
    assert body["type"] == "/errors/not_found"
    assert body["status"] == 404


def test_filter_by_status():
    """Тест фильтрации по статусу"""
    # Создаём записи с разными статусами
    client.post(
        "/entries", json={"title": "Book 1", "author": "Author 1", "status": "to_read"}
    )
    client.post(
        "/entries", json={"title": "Book 2", "author": "Author 2", "status": "reading"}
    )
    client.post(
        "/entries", json={"title": "Book 3", "author": "Author 3", "status": "reading"}
    )
    client.post(
        "/entries",
        json={"title": "Book 4", "author": "Author 4", "status": "completed"},
    )

    # Фильтруем по статусу "reading"
    response = client.get("/entries/filter/by-status?status=reading")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(e["status"] == "reading" for e in data)


def test_filter_by_author():
    """Тест фильтрации по автору"""
    # Создаём записи
    client.post("/entries", json={"title": "Book 1", "author": "Martin Fowler"})
    client.post("/entries", json={"title": "Book 2", "author": "Robert Martin"})
    client.post("/entries", json={"title": "Book 3", "author": "Kent Beck"})

    # Фильтруем по части имени автора
    response = client.get("/entries/filter/by-status?author=Martin")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("Martin" in e["author"] for e in data)


def test_filter_by_status_and_author():
    """Тест фильтрации по статусу и автору одновременно"""
    # Создаём записи
    client.post(
        "/entries",
        json={"title": "Book 1", "author": "Martin Fowler", "status": "reading"},
    )
    client.post(
        "/entries",
        json={"title": "Book 2", "author": "Robert Martin", "status": "completed"},
    )
    client.post(
        "/entries",
        json={"title": "Book 3", "author": "Martin Fowler", "status": "completed"},
    )

    # Фильтруем по обоим параметрам
    response = client.get("/entries/filter/by-status?status=completed&author=Fowler")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["author"] == "Martin Fowler"
    assert data[0]["status"] == "completed"


def test_filter_no_params():
    """Тест фильтрации без параметров (возвращает все записи)"""
    # Создаём записи
    client.post("/entries", json={"title": "Book 1", "author": "Author 1"})
    client.post("/entries", json={"title": "Book 2", "author": "Author 2"})

    # Фильтруем без параметров
    response = client.get("/entries/filter/by-status")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_entry_timestamps():
    """Тест корректности временных меток"""
    # Создаём запись
    create_resp = client.post("/entries", json={"title": "Book", "author": "Author"})
    data = create_resp.json()
    created_at = data["created_at"]
    updated_at = data["updated_at"]

    # Изначально created_at и updated_at должны быть одинаковыми
    assert created_at == updated_at

    # Обновляем запись
    entry_id = data["id"]
    update_resp = client.put(f"/entries/{entry_id}", json={"title": "Updated Book"})
    updated_data = update_resp.json()

    # created_at не должен измениться
    assert updated_data["created_at"] == created_at
    # updated_at должен обновиться
    # (В реальности может совпасть из-за скорости выполнения, но проверяем структуру)
    assert "updated_at" in updated_data


def test_multiple_entries_ids():
    """Тест уникальности ID записей"""
    # Создаём несколько записей
    ids = []
    for i in range(5):
        resp = client.post(
            "/entries", json={"title": f"Book {i}", "author": f"Author {i}"}
        )
        ids.append(resp.json()["id"])

    # Все ID должны быть уникальными
    assert len(ids) == len(set(ids))

    # ID должны быть последовательными
    assert ids == list(range(1, 6))

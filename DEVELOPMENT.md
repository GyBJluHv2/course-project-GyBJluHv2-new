# Инструкции для разработки

## Настройка окружения

### 1. Создание виртуального окружения

```bash
python -m venv venv
```

### 2. Активация виртуального окружения

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

После активации вы увидите `(venv)` в начале строки командной строки.

### 3. Установка зависимостей

```bash
# Основные зависимости
pip install -r requirements.txt

# Зависимости для разработки
pip install -r requirements-dev.txt
```

---

## Работа с проектом

**⚠️ ВАЖНО:** Все команды ниже нужно выполнять **с активированным виртуальным окружением!**

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Конкретный файл с тестами
pytest tests/test_reading_list.py -v

# С покрытием кода
pytest --cov=app tests/
```

### Проверка качества кода

```bash
# Линтер
ruff check .

# Форматирование (проверка)
ruff format --check .

# Применить форматирование
ruff format .

# Запуск всех pre-commit хуков
pre-commit run --all-files
```

### Запуск приложения

```bash
# Режим разработки (с автоперезагрузкой)
uvicorn app.main:app --reload

# Обычный запуск
uvicorn app.main:app
```

Приложение будет доступно по адресу: http://127.0.0.1:8000

**Swagger UI (интерактивная документация):** http://127.0.0.1:8000/docs

---

## Рабочий процесс для P02

### 1. Создайте ветку

```bash
git checkout main
git pull
git checkout -b p02-reading-list
```

### 2. Убедитесь, что всё работает

```bash
# Активируйте venv
.\venv\Scripts\Activate.ps1

# Запустите тесты
pytest tests/ -v

# Проверьте линтеры
ruff check .
ruff format --check .

# Запустите pre-commit
pre-commit run --all-files
```

### 3. Сделайте коммиты

```bash
git add app/models.py
git commit -m "feat: add Entry models for reading list"

git add app/main.py
git commit -m "feat: implement CRUD endpoints for reading list entries"

git add tests/test_reading_list.py
git commit -m "test: add comprehensive tests for reading list API"

git add .gitignore DEVELOPMENT.md
git commit -m "docs: add development instructions and update gitignore"
```

### 4. Отправьте изменения

```bash
git push origin p02-reading-list
```

### 5. Создайте Pull Request на GitHub

Перейдите на GitHub и создайте PR из ветки `p02-reading-list` в `main`.

---

## Полезные команды

### Деактивация виртуального окружения

```bash
deactivate
```

### Обновление зависимостей

```bash
pip install --upgrade -r requirements.txt -r requirements-dev.txt
```

### Проверка установленных пакетов

```bash
pip list
```

### Экспорт текущих зависимостей

```bash
pip freeze > requirements-freeze.txt
```

---

## Устранение проблем

### Проблема: "pytest: command not found"

**Решение:** Убедитесь, что виртуальное окружение активировано. Должен быть префикс `(venv)`.

### Проблема: "ModuleNotFoundError"

**Решение:** Установите зависимости:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Проблема: PowerShell блокирует выполнение скриптов

**Решение:** Выполните от имени администратора:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Структура проекта

```
course-project-GyBJluHv2/
├── app/
│   ├── __init__.py
│   ├── main.py          # Основное приложение FastAPI
│   └── models.py        # Pydantic модели
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_errors.py
│   └── test_reading_list.py
├── venv/                # Виртуальное окружение (не в Git)
├── requirements.txt     # Основные зависимости
├── requirements-dev.txt # Зависимости для разработки
├── pyproject.toml       # Конфигурация инструментов
├── .gitignore
└── DEVELOPMENT.md       # Этот файл
```


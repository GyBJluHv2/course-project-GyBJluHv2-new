from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReadingStatus(str, Enum):
    """Статус прочтения книги"""

    TO_READ = "to_read"
    READING = "reading"
    COMPLETED = "completed"


class EntryCreate(BaseModel):
    """Схема создания записи"""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Название книги/статьи"
    )
    author: str = Field(..., min_length=1, max_length=100, description="Автор")
    status: ReadingStatus = Field(
        default=ReadingStatus.TO_READ, description="Статус прочтения"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Заметки")


class EntryUpdate(BaseModel):
    """Схема обновления записи"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[ReadingStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class Entry(BaseModel):
    """Полная модель записи"""

    id: int
    title: str
    author: str
    status: ReadingStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

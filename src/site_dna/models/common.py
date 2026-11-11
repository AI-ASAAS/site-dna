"""Shared Phase 1 report contracts used by every analyzer module."""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class ModuleStatus(str, Enum):
    """Normalized outcome of a single analyzer module."""

    ok = "ok"
    partial = "partial"
    failed = "failed"
    skipped = "skipped"
    not_available = "not_available"


class ModuleError(BaseModel):
    """Structured module error that never leaks a traceback into the report."""

    code: str
    message: str
    url: str | None = None


T = TypeVar("T")


class ModuleResult(BaseModel, Generic[T]):
    """Uniform envelope returned by every module boundary."""

    status: ModuleStatus
    reason: str | None = None
    duration_ms: int
    data: T | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[ModuleError] = Field(default_factory=list)


class FileRef(BaseModel):
    """Reference to an artifact stored on disk instead of inside the report."""

    path: str
    format: str
    bytes: int
    sha256: str
    width: int | None = None
    height: int | None = None


class CheckStatus(str, Enum):
    """Outcome of a single SEO rule or check."""

    passed = "passed"
    warning = "warning"
    failed = "failed"
    not_available = "not_available"

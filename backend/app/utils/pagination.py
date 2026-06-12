from dataclasses import dataclass
from math import ceil

from fastapi import Query

from app.core.config import settings


@dataclass
class PaginationParams:
    """
    Parsed and validated pagination parameters from query string.
    Injected via FastAPI Depends().
    """
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=None,
        ge=1,
        description="Items per page",
    ),
) -> PaginationParams:
    """
    FastAPI dependency for pagination query params.

    Usage:
        pagination: PaginationParams = Depends(get_pagination)
    """
    size = page_size or settings.default_page_size
    size = min(size, settings.max_page_size)
    return PaginationParams(page=page, page_size=size)


@dataclass
class PaginatedResponse:
    """
    Wraps a list of items with pagination metadata.
    Used as a return value from service list methods.
    """
    items: list
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.page_size) if self.page_size else 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
            },
        }
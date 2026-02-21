---
paths:
  - "**/*.py"
---

# Python Rules

- Use type hints on all public function signatures.
- Use Pydantic v2 models for all data validation (BaseModel, not dataclass for API schemas).
- Prefer `async def` for I/O-bound functions (DB, HTTP, file I/O).
- Use `Annotated[type, Depends()]` for FastAPI dependency injection.
- Separate Pydantic schemas: `CreateFoo`, `UpdateFoo`, `FooResponse` (never reuse one model for all).
- SQLAlchemy: use `selectinload` or `joinedload` to avoid N+1 queries.
- Error handling: raise custom exceptions that map to HTTP status codes, handle in exception handlers.
- Tests: `pytest` with `pytest-asyncio`, use `httpx.AsyncClient` for API tests.
- Imports: group as stdlib → third-party → local, one blank line between groups.
- Use `uv` as package manager, not pip.
- Format with ruff. No manual formatting.

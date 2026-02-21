# LeGM-Lab

## Stack
- Backend: Python 3.12+ / FastAPI / SQLAlchemy / Pydantic v2
- Frontend: Next.js 15 / TypeScript / Tailwind CSS / shadcn/ui
- ML: PyTorch / HuggingFace Transformers / W&B for experiment tracking
- Database: PostgreSQL (prod), SQLite (dev/experiments)
- Testing: pytest + pytest-asyncio + httpx (backend), Vitest + React Testing Library (frontend)
- Package managers: uv (Python), bun (JS/TS)

## Commands
- `uv run pytest` — run backend tests
- `uv run pytest -x -v` — run tests, stop on first failure
- `bun test` — run frontend tests
- `bun dev` — start Next.js dev server
- `ruff check --fix . && ruff format .` — lint + format Python
- `bunx prettier --write .` — format frontend code
- `uv run python -m mypy .` — type check Python

## Code Style
- Python: ruff rules, type hints on all public functions, docstrings on modules/classes
- TypeScript: strict mode, no `any`, prefer `interface` over `type` for object shapes
- Components: functional only, named exports, co-locate tests next to source
- Imports: absolute imports preferred, group stdlib / third-party / local

## Conventions
- Branch naming: `feat/`, `fix/`, `chore/`, `exp/` (experiments)
- Commit style: conventional commits (feat:, fix:, chore:, docs:, test:)
- PR descriptions must include a test plan section
- All API endpoints need OpenAPI descriptions
- ML experiments must log hyperparams, metrics, and model checkpoints

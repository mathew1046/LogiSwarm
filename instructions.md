# LogiSwarm — Dev Instructions

## Core Rules
- Follow `PLAN.md` task by task, in order. Don't skip ahead.
- After every task: update `project.md` status + add one line to `changelog.md` (top).
- Commit using the exact message from `PLAN.md`.
- create multiple small commits for each task with meaning full messages.

## Code Quality
- Write clean, readable code. Prefer clarity over cleverness.
- No unused imports, dead code, or commented-out blocks.
- Every function needs a docstring if it's non-obvious.
- Use type hints everywhere in Python. Use TypeScript types in frontend.
- Pydantic for all API input/output schemas — no raw dicts crossing API boundaries.
- All async — no blocking calls in agent loops.

## File Hygiene
- Do NOT create throwaway `.md` files, test scripts, or scratch `.py` files.
- Do NOT leave `debug.py`, `test_quick.py`, `temp.py`, or similar files in the repo.
- Remove a file the moment it becomes redundant. Dead code = technical debt.
- Only these top-level files are allowed: `README.md`, `PLAN.md`, `project.md`, `instructions.md`, `changelog.md`, `CHANGELOG.md`, `.env.example`, `docker-compose.yml`, `package.json`, `LICENSE`.

## Environment
- All secrets in `.env`, never hardcoded. Never commit `.env`.
- `.env.example` must stay updated with every new variable added.
- Config validation on startup — fail fast with a clear message if required vars are missing.

## Git
- Commit messages: conventional commits format (`feat:`, `fix:`, `refactor:`, `style:`, `test:`, `docs:`, `chore:`).
- Never commit: `.env`, `__pycache__`, `node_modules`, build artifacts, model weights.
- Branch: work on `main` for solo dev. Use feature branches when collaborating.

## Backend
- FastAPI + async SQLAlchemy. No raw SQL with user input — ORM only.
- Endpoints return consistent envelopes: `{data, error, meta}`.
- All list endpoints must be paginated from day one.
- Log every LLM call: model, tokens in/out, latency, cost estimate.
- Agents sleep between cycles — never spin in a tight loop.

## Frontend
- Vue 3 Composition API only. No Options API.
- Every data-fetching component must handle: loading, error, empty states.
- No hardcoded colors — CSS variables only (dark mode support built-in).
- Lazy-load all route components.

## LLM Usage
- Structured JSON output via tool use — never parse free-text LLM responses.
- Always set a semaphore (max concurrent calls). Always log usage.
- Prompt changes count as code changes — commit them.

## Testing
- New feed connector = add a mock test.
- New agent behavior = add a unit test with mocked LLM response.
- Don't merge broken tests.

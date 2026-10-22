# life-projects-api
The Projects and portfolio cell: its own API (Railway, serverless) and its own Neon
database, described by `cell.yaml` and served by the code in `src/cellkit/`, which
this repository owns. It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `life-projects-api`, service `projects-api` (Serverless) |
| Publisher | service `projects-publisher` (Railway cron, `*/15 * * * *`) |
| Data | Neon project `life-projects-api`, database `projects` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`projects`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `projects.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/projects` | project | `status`, `category`, `type`, `domain`, `priority`, `parent_project_id` |
| `/v1/project-repos` | project-repo | `project_id`, `role`, `is_primary` |
| `/v1/portfolio-contexts` | portfolio-context | `context_type`, `scope`, `status`, `parent_context_id` |
| `/v1/project-context-links` | project-context-link | `project_id`, `context_id`, `relation_type` |
| `/v1/work-items` | work-item | `item_type`, `status`, `goal_id`, `project_id`, `parent_item_id`, `source_key` |
| `/v1/work-item-task-links` | work-item-task-link | `work_item_id`, `task_id`, `relation_type` |
| `/v1/work-item-goal-task-links` | work-item-goal-task-link | `work_item_id`, `goal_task_id`, `relation_type` |

## Develop and operate

```bash
uv sync --frozen --all-extras          # Python 3.12 (.python-version): pgserver has no cp313 wheel yet
.venv/bin/pytest -q
.venv/bin/mypy . && uvx ruff@0.17.1 check . && uvx ruff@0.17.1 format --check .   # the same checks CI runs
NEON_API_KEY=... .venv/bin/projects-db provision
npm install && railway config apply   # service settings only; code deploys from GitHub (below)
```

Dependencies are locked in `uv.lock`; the image installs them with `uv sync --frozen`, so
production runs the versions CI tested. Change a dependency with `uv add`/`uv lock` and commit
the lock. Product scope and measures: [PRODUCT.md](PRODUCT.md); change records: `specs/`.

Deploys (CD, since 2026-10-18): `projects-api` and `projects-publisher` are connected to this
repository's `main` with Railway's Wait for CI (`checkSuites`). A merge to `main` deploys only
after the CI and security checks pass; a failing check leaves production on the previous
deployment. Roll back by redeploying an earlier deployment in Railway. `railway up` is no
longer used.

Railway variables: `SENTRY_DSN` (error reporting; unset = off, see
`src/cellkit/_sentry.py`), `PROJECTS_DB_MODE=hosted`, `PROJECTS_DB_URL_API`,
`PROJECTS_JWT_PUBLIC_KEY_PEM`, `PROJECTS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`, and for the publisher `PROJECTS_DB_URL_PUBLISHER` and `PROJECTS_PUBLISHER_TOKEN`.

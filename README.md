# solo-projects

The Projects and portfolio cell: its own API (Railway, serverless) and its own Neon
database, made from `cell.yaml` with [solo-cell-kit](../solo-cell-kit). It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `solo-projects`, service `projects-api` (Serverless) |
| Publisher | service `projects-publisher` (Railway cron, `*/15 * * * *`) |
| Data | Neon project `solo-projects`, database `projects` |
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
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/projects-db provision
npm install && railway config apply && railway up --ci --service projects-api
```

Railway variables: `PROJECTS_DB_MODE=hosted`, `PROJECTS_DB_URL_API`,
`PROJECTS_JWT_PUBLIC_KEY_PEM`, `PROJECTS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`, and for the publisher `PROJECTS_DB_URL_PUBLISHER` and `PROJECTS_PUBLISHER_TOKEN`.

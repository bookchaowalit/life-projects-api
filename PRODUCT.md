# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through the cell's own MCP server (`projects-mcp`) and the hosted tool
  hub (`platform-mcp-remote-worker`, which lists this service's host in its allow-list).
- Local tooling that reads the cell through `EMPIRE_PROJECTS_API`: `ops-toolkit`
  (`cell_store.py`) and `mcp-aggregator` (`cell-store.ts`), as recorded in the online-systems
  registry.
- Other cells that refer to projects and contexts by id: the roles-and-skills cell keeps
  `project_id` and `context_id` as plain numbers (not foreign keys); work items point at goals
  (`goal_id`), tasks (`task_id`) and goal tasks (`goal_task_id`) the same way.
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `projects.<resource>:read|write|delete` for each of the eight resources.
- A web page that shows projects or the portfolio: [ต้องยืนยัน].

## Product Purpose

The list of the owner's projects and where they live (repositories), the portfolio contexts they
belong to (personal, freelance, startup, client engagement and so on, which can nest), and the
work items (epics and stories) that break a project down, each linked to tasks and goal tasks that
implement or support it.

Success: each project exists once with a status and progress, belongs to a context, and its work
items trace to the tasks that deliver them.

## Positioning

One capability, one service: its own API (Railway, serverless) with a publisher cron, its own
database (Neon) with row-level security per workspace, and authorization, executions and audit
through `empire-platform`. It is workspace-scoped, so the same service can serve other tenants
without code changes.

## Operating Context

- Production: `https://projects-api-production-f4eb.up.railway.app` (`/health`), deployed by
  merging to `main` after CI. The `projects-publisher` cron (every 15 minutes) delivers graph
  events for projects, contexts and work items.
- About 516 rows were imported from the retired SQLite tables keeping their ids (`legacy_id`).
- Monitored by `platform-uptime-worker` (target `projects-api`); errors go to Sentry without
  personal data.

## Capabilities and Constraints

- Resources, each with list, stats, get, get-by-legacy-id, create (with `Idempotency-Key`), patch
  (with `expected_version`) and delete: `/v1/projects`, `/v1/project-repos`,
  `/v1/portfolio-contexts`, `/v1/project-context-links`, `/v1/work-items`,
  `/v1/work-item-task-links` and `/v1/work-item-goal-task-links`. Filters are the ones in the
  README; stats group by a filter only.
- Project rules: `name` and `slug` are required and `slug` is unique; `category`
  (product, client, internal, experiment, portfolio, open_source) and `status` (idea, planning,
  active, paused, completed, abandoned, archived) are fixed enums; new projects are product ideas
  at priority 3; `progress_percent` is 0 to 100; dates are real dates; a project may have a parent
  project in the same workspace. No order between `start_date`, `target_launch`, `launched_at`
  and `completed_at` is enforced.
- Repository rules: `repo_name` is required (at most 300 characters) and unique within a project;
  `role` is frontend, backend, fullstack, docs, infra, script, mobile or other. Repositories with
  no project are not deduplicated.
- Context rules: `slug` is unique; `context_type` is required and one of twelve kinds; `scope`
  defaults to personal and `status` to active. A project links to a context once; `weight` must be
  at least 0.0001.
- Work item rules: `item_type` (epic or story), `title`, `project_id` and `source_key` are
  required and `source_key` is unique across all work items; `progress_percent` is 0 to 100;
  `weight` is at least 0.0001; `parent_item_id` and `project_id` must exist in the same workspace.
  A work item links to a task, and to a goal task, once each.
- A project, context or work item that other records point at cannot be deleted until they are
  removed (409 `has_dependents`). Unknown fields are refused (422); an unchanged patch keeps the
  version.
- Out of scope: checking that `goal_id`, `task_id` and `goal_task_id` exist in their own services,
  computing `progress_percent`, `task_count` or revenue from other data, and cloning repositories.

## Measures

Proposed, nothing collects them yet:

- Active projects with at least one context link and one primary repository.
- Work items not done whose project is completed or archived (target: 0).
- 5xx rate and p95 latency on `/v1/projects` (Sentry and uptime worker).

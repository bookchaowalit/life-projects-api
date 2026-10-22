"""Shared helpers for the projects-and-portfolio domain tests."""

import uuid
from typing import Any

PROJECTS = "/v1/projects"
PROJECT_REPOS = "/v1/project-repos"
CONTEXTS = "/v1/portfolio-contexts"
CONTEXT_LINKS = "/v1/project-context-links"
WORK_ITEMS = "/v1/work-items"
TASK_LINKS = "/v1/work-item-task-links"
GOAL_TASK_LINKS = "/v1/work-item-goal-task-links"


def unique(prefix: str = "x") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def other_workspace(harness: Any, platform: Any) -> dict[str, str]:
    """A token of another workspace whose actor may do everything there."""
    actor = uuid.uuid4()
    platform.grants[actor] = set(harness.cell.permissions())
    return harness.token(actor, uuid.uuid4())


def make(
    client: Any, headers: dict[str, str], path: str, **body: Any
) -> dict[str, Any]:
    response = client.post(path, headers=headers, json=body)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_project(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"name": "Website", "slug": unique("proj"), **fields}
    return client.post(PROJECTS, headers=owner, json=body)


def new_project(client: Any, owner: dict[str, str], **fields: Any) -> dict[str, Any]:
    response = create_project(client, owner, **fields)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_repo(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"repo_name": unique("repo"), **fields}
    return client.post(PROJECT_REPOS, headers=owner, json=body)


def create_context(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "slug": unique("ctx"),
        "name": "Freelance",
        "context_type": "freelance",
        **fields,
    }
    return client.post(CONTEXTS, headers=owner, json=body)


def new_context(client: Any, owner: dict[str, str], **fields: Any) -> dict[str, Any]:
    response = create_context(client, owner, **fields)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_context_link(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    return client.post(CONTEXT_LINKS, headers=owner, json=fields)


def create_work_item(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "item_type": "story",
        "title": "Write the page",
        "source_key": unique("key"),
        **fields,
    }
    return client.post(WORK_ITEMS, headers=owner, json=body)


def new_work_item(client: Any, owner: dict[str, str], **fields: Any) -> dict[str, Any]:
    if "project_id" not in fields:
        fields["project_id"] = new_project(client, owner)["id"]
    response = create_work_item(client, owner, **fields)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created

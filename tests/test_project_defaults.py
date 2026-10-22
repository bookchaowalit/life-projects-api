"""Defaults, uniqueness and imports of projects and their repositories."""

from projects_helpers import (
    PROJECT_REPOS,
    PROJECTS,
    create_project,
    create_repo,
    make,
    new_project,
    unique,
)


def test_new_project_starts_as_a_product_idea_with_nothing_done(client, owner):
    response = create_project(client, owner)
    assert response.status_code == 201, response.text
    project = response.json()
    assert project["category"] == "product"
    assert project["status"] == "idea"
    assert project["priority"] == 3
    assert project["progress_percent"] == 0
    assert project["monthly_revenue"] == 0
    assert project["total_revenue"] == 0
    assert project["task_count"] == 0
    assert project["completed_count"] == 0
    assert project["parent_project_id"] is None
    assert project["archived_at"] is None
    assert project["version"] == 1


def test_project_slug_is_unique(client, owner):
    slug = unique("taken")
    assert create_project(client, owner, slug=slug).status_code == 201
    assert create_project(client, owner, slug=slug, name="Other").status_code == 409


def test_projects_may_share_a_name(client, owner):
    assert create_project(client, owner, name="Same").status_code == 201
    assert create_project(client, owner, name="Same").status_code == 201


def test_a_project_can_have_a_parent(client, owner):
    parent = new_project(client, owner)
    child = create_project(client, owner, parent_project_id=parent["id"])
    assert child.status_code == 201, child.text
    assert child.json()["parent_project_id"] == parent["id"]


def test_revenue_keeps_its_decimal_value(client, owner):
    project = new_project(client, owner, monthly_revenue=1234.5, total_revenue=9876.25)
    assert project["monthly_revenue"] == 1234.5
    assert project["total_revenue"] == 9876.25


def test_project_import_keeps_the_old_id(client, owner):
    imported = create_project(client, owner, legacy_id=6543)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 6543
    found = client.get(f"{PROJECTS}/legacy/6543", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 6543
    assert create_project(client, owner, legacy_id=6543).status_code == 409


def test_new_repository_is_a_secondary_fullstack_repository(client, owner):
    project = new_project(client, owner)
    response = create_repo(client, owner, project_id=project["id"])
    assert response.status_code == 201, response.text
    repo = response.json()
    assert repo["role"] == "fullstack"
    assert repo["is_primary"] is False
    assert repo["repo_url"] is None
    assert repo["version"] == 1


def test_a_project_lists_a_repository_name_only_once(client, owner):
    project = new_project(client, owner)
    ids = {"project_id": project["id"], "repo_name": "web-app"}
    make(client, owner, PROJECT_REPOS, **ids)
    assert client.post(PROJECT_REPOS, headers=owner, json=ids).status_code == 409
    other_name = create_repo(client, owner, project_id=project["id"], repo_name="api")
    assert other_name.status_code == 201, other_name.text


def test_two_projects_can_use_the_same_repository_name(client, owner):
    first, second = new_project(client, owner), new_project(client, owner)
    for project in (first, second):
        repo = create_repo(client, owner, project_id=project["id"], repo_name="shared")
        assert repo.status_code == 201, repo.text


def test_repositories_without_a_project_are_not_deduplicated(client, owner):
    # The unique key includes project_id, and the database treats empty values as different.
    first = create_repo(client, owner, repo_name="orphan")
    second = create_repo(client, owner, repo_name="orphan")
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

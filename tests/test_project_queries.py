"""Listing, grouping and the lifecycle of projects and their repositories."""

from projects_helpers import (
    PROJECT_REPOS,
    PROJECTS,
    create_repo,
    new_project,
    unique,
)


def test_list_filters_projects_by_status_category_type_domain_and_priority(
    client, owner
):
    domain = unique("domain")
    mine = new_project(
        client,
        owner,
        status="active",
        category="client",
        type="website",
        domain=domain,
        priority=1,
    )
    new_project(client, owner, status="paused", category="internal", domain=domain)
    for params in (
        {"domain": domain, "status": "active"},
        {"domain": domain, "category": "client"},
        {"domain": domain, "type": "website"},
        {"domain": domain, "priority": 1},
    ):
        listed = client.get(PROJECTS, headers=owner, params=params)
        assert listed.status_code == 200, listed.text
        assert [p["id"] for p in listed.json()["items"]] == [mine["id"]], params


def test_list_finds_the_children_of_a_project(client, owner):
    parent = new_project(client, owner)
    child = new_project(client, owner, parent_project_id=parent["id"])
    new_project(client, owner)
    listed = client.get(
        PROJECTS, headers=owner, params={"parent_project_id": parent["id"]}
    )
    assert [p["id"] for p in listed.json()["items"]] == [child["id"]]


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    assert client.get(PROJECTS, headers=owner, params={"slug": "x"}).status_code == 422


def test_list_is_in_creation_order_and_can_be_reversed(client, owner):
    ids = [new_project(client, owner)["id"] for _ in range(3)]
    ascending = client.get(PROJECTS, headers=owner, params={"id": ids})
    assert [p["id"] for p in ascending.json()["items"]] == ids
    descending = client.get(
        PROJECTS, headers=owner, params={"id": ids, "order": "desc"}
    )
    assert [p["id"] for p in descending.json()["items"]] == ids[::-1]


def test_stats_count_projects_per_status_and_category(client, owner):
    new_project(client, owner, status="abandoned", category="experiment")
    by_status = client.get(
        f"{PROJECTS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert by_status.status_code == 200, by_status.text
    assert by_status.json()["groups"]["abandoned"] >= 1
    by_category = client.get(
        f"{PROJECTS}/stats", headers=owner, params={"group_by": "category"}
    )
    assert by_category.json()["groups"]["experiment"] >= 1


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(f"{PROJECTS}/stats", headers=owner, params={"group_by": "name"})
    assert stats.status_code == 422


def test_launching_a_project_keeps_its_other_data(client, owner):
    project = new_project(client, owner, status="active", target_launch="2026-11-01")
    path = f"{PROJECTS}/{project['id']}"
    launched = client.patch(
        path,
        headers=owner,
        json={
            "status": "completed",
            "launched_at": "2026-11-02",
            "progress_percent": 100,
        },
    )
    assert launched.status_code == 200, launched.text
    assert launched.json()["version"] == 2
    assert launched.json()["target_launch"] == "2026-11-01"
    unchanged = client.patch(path, headers=owner, json={"status": "completed"})
    assert unchanged.json()["version"] == 2


def test_a_stale_expected_version_is_refused(client, owner):
    project = new_project(client, owner)
    path = f"{PROJECTS}/{project['id']}"
    client.patch(path, headers=owner, json={"notes": "first"})
    stale = client.patch(
        path, headers=owner, json={"notes": "second", "expected_version": 1}
    )
    assert stale.status_code == 409


def test_a_project_with_repositories_or_children_cannot_be_deleted(client, owner):
    project = new_project(client, owner)
    path = f"{PROJECTS}/{project['id']}"
    repo = create_repo(client, owner, project_id=project["id"]).json()
    blocked = client.delete(path, headers=owner)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == {"error": "has_dependents"}
    assert (
        client.delete(f"{PROJECT_REPOS}/{repo['id']}", headers=owner).status_code == 204
    )
    child = new_project(client, owner, parent_project_id=project["id"])
    assert client.delete(path, headers=owner).status_code == 409
    assert client.delete(f"{PROJECTS}/{child['id']}", headers=owner).status_code == 204
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_repositories_are_listed_by_project_role_and_primary(client, owner):
    project = new_project(client, owner)
    web = create_repo(
        client,
        owner,
        project_id=project["id"],
        repo_name="web",
        role="frontend",
        is_primary=True,
    ).json()
    api = create_repo(
        client, owner, project_id=project["id"], repo_name="api", role="backend"
    ).json()
    by_project = client.get(
        PROJECT_REPOS, headers=owner, params={"project_id": project["id"]}
    )
    assert {r["id"] for r in by_project.json()["items"]} == {web["id"], api["id"]}
    by_role = client.get(
        PROJECT_REPOS,
        headers=owner,
        params={"project_id": project["id"], "role": "backend"},
    )
    assert [r["id"] for r in by_role.json()["items"]] == [api["id"]]
    primary = client.get(
        PROJECT_REPOS,
        headers=owner,
        params={"project_id": project["id"], "is_primary": "true"},
    )
    assert [r["id"] for r in primary.json()["items"]] == [web["id"]]
    assert (
        client.get(
            PROJECT_REPOS, headers=owner, params={"is_primary": "maybe"}
        ).status_code
        == 422
    )


def test_repository_stats_group_by_role_and_refuse_other_fields(client, owner):
    create_repo(client, owner, role="infra")
    stats = client.get(
        f"{PROJECT_REPOS}/stats", headers=owner, params={"group_by": "role"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["infra"] >= 1
    refused = client.get(
        f"{PROJECT_REPOS}/stats", headers=owner, params={"group_by": "language"}
    )
    assert refused.status_code == 422


def test_a_repository_can_become_primary_and_be_deleted(client, owner):
    repo = create_repo(client, owner).json()
    path = f"{PROJECT_REPOS}/{repo['id']}"
    primary = client.patch(path, headers=owner, json={"is_primary": True})
    assert primary.status_code == 200, primary.text
    assert primary.json()["is_primary"] is True
    assert primary.json()["version"] == 2
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404

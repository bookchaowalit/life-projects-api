"""Listing, grouping and the lifecycle of portfolio contexts and project-context links."""

from projects_helpers import (
    CONTEXT_LINKS,
    CONTEXTS,
    create_context_link,
    new_context,
    new_project,
)


def test_list_filters_contexts_by_type_scope_status_and_parent(client, owner):
    parent = new_context(client, owner)
    mine = new_context(
        client,
        owner,
        context_type="startup",
        scope="professional",
        status="paused",
        parent_context_id=parent["id"],
    )
    new_context(client, owner, context_type="hobby", parent_context_id=parent["id"])
    for params in (
        {"parent_context_id": parent["id"], "context_type": "startup"},
        {"parent_context_id": parent["id"], "scope": "professional"},
        {"parent_context_id": parent["id"], "status": "paused"},
    ):
        listed = client.get(CONTEXTS, headers=owner, params=params)
        assert listed.status_code == 200, listed.text
        assert [c["id"] for c in listed.json()["items"]] == [mine["id"]], params


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    assert client.get(CONTEXTS, headers=owner, params={"slug": "x"}).status_code == 422


def test_stats_count_contexts_per_type_and_scope(client, owner):
    new_context(client, owner, context_type="role_capability", scope="mixed")
    by_type = client.get(
        f"{CONTEXTS}/stats", headers=owner, params={"group_by": "context_type"}
    )
    assert by_type.status_code == 200, by_type.text
    assert by_type.json()["groups"]["role_capability"] >= 1
    by_scope = client.get(
        f"{CONTEXTS}/stats", headers=owner, params={"group_by": "scope"}
    )
    assert by_scope.json()["groups"]["mixed"] >= 1
    refused = client.get(
        f"{CONTEXTS}/stats", headers=owner, params={"group_by": "name"}
    )
    assert refused.status_code == 422


def test_archiving_a_context_bumps_the_version_once(client, owner):
    context = new_context(client, owner)
    path = f"{CONTEXTS}/{context['id']}"
    archived = client.patch(path, headers=owner, json={"status": "archived"})
    assert archived.status_code == 200, archived.text
    assert archived.json()["version"] == 2
    unchanged = client.patch(path, headers=owner, json={"status": "archived"})
    assert unchanged.json()["version"] == 2


def test_a_context_with_children_or_links_cannot_be_deleted(client, owner):
    context = new_context(client, owner)
    path = f"{CONTEXTS}/{context['id']}"
    child = new_context(client, owner, parent_context_id=context["id"])
    assert client.delete(path, headers=owner).status_code == 409
    assert client.delete(f"{CONTEXTS}/{child['id']}", headers=owner).status_code == 204
    project = new_project(client, owner)
    link = create_context_link(
        client, owner, project_id=project["id"], context_id=context["id"]
    ).json()
    blocked = client.delete(path, headers=owner)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == {"error": "has_dependents"}
    assert (
        client.delete(f"{CONTEXT_LINKS}/{link['id']}", headers=owner).status_code == 204
    )
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_context_links_are_listed_by_project_context_and_relation(client, owner):
    project, other_project = new_project(client, owner), new_project(client, owner)
    context = new_context(client, owner)
    primary = create_context_link(
        client, owner, project_id=project["id"], context_id=context["id"]
    ).json()
    supporting = create_context_link(
        client,
        owner,
        project_id=other_project["id"],
        context_id=context["id"],
        relation_type="supporting",
    ).json()
    by_context = client.get(
        CONTEXT_LINKS, headers=owner, params={"context_id": context["id"]}
    )
    assert {x["id"] for x in by_context.json()["items"]} == {
        primary["id"],
        supporting["id"],
    }
    by_project = client.get(
        CONTEXT_LINKS, headers=owner, params={"project_id": project["id"]}
    )
    assert [x["id"] for x in by_project.json()["items"]] == [primary["id"]]
    by_relation = client.get(
        CONTEXT_LINKS,
        headers=owner,
        params={"context_id": context["id"], "relation_type": "supporting"},
    )
    assert [x["id"] for x in by_relation.json()["items"]] == [supporting["id"]]


def test_context_link_stats_group_by_relation_and_refuse_other_fields(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    create_context_link(
        client,
        owner,
        project_id=project["id"],
        context_id=context["id"],
        relation_type="supporting",
    )
    stats = client.get(
        f"{CONTEXT_LINKS}/stats", headers=owner, params={"group_by": "relation_type"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["supporting"] >= 1
    refused = client.get(
        f"{CONTEXT_LINKS}/stats", headers=owner, params={"group_by": "weight"}
    )
    assert refused.status_code == 422


def test_a_context_link_can_be_reweighted_and_deleted(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    link = create_context_link(
        client, owner, project_id=project["id"], context_id=context["id"]
    ).json()
    path = f"{CONTEXT_LINKS}/{link['id']}"
    changed = client.patch(path, headers=owner, json={"weight": 0.5})
    assert changed.status_code == 200, changed.text
    assert changed.json()["weight"] == 0.5
    assert changed.json()["version"] == 2
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404

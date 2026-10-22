"""Defaults and uniqueness of portfolio contexts and project-context links."""

from projects_helpers import (
    CONTEXTS,
    create_context,
    create_context_link,
    new_context,
    new_project,
    unique,
)


def test_new_context_is_an_active_personal_context(client, owner):
    response = create_context(client, owner)
    assert response.status_code == 201, response.text
    context = response.json()
    assert context["scope"] == "personal"
    assert context["status"] == "active"
    assert context["source"] == "manual"
    assert context["parent_context_id"] is None
    assert context["version"] == 1


def test_context_slug_is_unique(client, owner):
    slug = unique("taken")
    assert create_context(client, owner, slug=slug).status_code == 201
    assert create_context(client, owner, slug=slug, name="Other").status_code == 409


def test_contexts_may_share_a_name_and_type(client, owner):
    assert create_context(client, owner, name="Same").status_code == 201
    assert create_context(client, owner, name="Same").status_code == 201


def test_a_context_can_be_nested(client, owner):
    parent = new_context(client, owner)
    child = create_context(client, owner, parent_context_id=parent["id"])
    assert child.status_code == 201, child.text
    assert child.json()["parent_context_id"] == parent["id"]


def test_context_import_keeps_the_old_id(client, owner):
    imported = create_context(client, owner, legacy_id=8080)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 8080
    found = client.get(f"{CONTEXTS}/legacy/8080", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 8080
    assert create_context(client, owner, legacy_id=8080).status_code == 409


def test_new_context_link_is_primary_with_full_weight(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    response = create_context_link(
        client, owner, project_id=project["id"], context_id=context["id"]
    )
    assert response.status_code == 201, response.text
    link = response.json()
    assert link["relation_type"] == "primary"
    assert link["weight"] == 1
    assert link["source"] == "manual"
    assert link["version"] == 1


def test_a_project_links_to_a_context_only_once(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    ids = {"project_id": project["id"], "context_id": context["id"]}
    assert create_context_link(client, owner, **ids).status_code == 201
    assert (
        create_context_link(
            client, owner, **ids, relation_type="supporting"
        ).status_code
        == 409
    )


def test_a_project_can_join_several_contexts_and_a_context_hold_several_projects(
    client, owner
):
    project, other_project = new_project(client, owner), new_project(client, owner)
    first, second = new_context(client, owner), new_context(client, owner)
    for project_id, context_id in (
        (project["id"], first["id"]),
        (project["id"], second["id"]),
        (other_project["id"], first["id"]),
    ):
        response = create_context_link(
            client, owner, project_id=project_id, context_id=context_id
        )
        assert response.status_code == 201, response.text


def test_context_link_weight_keeps_its_decimal_value(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    link = create_context_link(
        client, owner, project_id=project["id"], context_id=context["id"], weight=0.25
    ).json()
    assert link["weight"] == 0.25

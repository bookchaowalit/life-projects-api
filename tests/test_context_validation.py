"""What portfolio contexts and project-context links refuse."""

from projects_helpers import (
    CONTEXT_LINKS,
    CONTEXTS,
    create_context,
    create_context_link,
    new_context,
    new_project,
    other_workspace,
    unique,
)

CONTEXT_TYPES = [
    "personal",
    "hobby",
    "learning",
    "freelance",
    "startup",
    "venture",
    "client_engagement",
    "internal",
    "business_system",
    "workspace",
    "role_capability",
    "unclassified",
]


def test_a_context_needs_a_slug_name_and_type(client, owner):
    complete = {"slug": unique("ctx"), "name": "Freelance", "context_type": "freelance"}
    for missing in complete:
        body = {k: v for k, v in complete.items() if k != missing}
        assert client.post(CONTEXTS, headers=owner, json=body).status_code == 422, (
            missing
        )


def test_context_type_must_be_a_known_kind(client, owner):
    for kind in CONTEXT_TYPES:
        assert create_context(client, owner, context_type=kind).status_code == 201, kind
    assert create_context(client, owner, context_type="hobbyist").status_code == 422


def test_context_scope_and_status_must_be_known(client, owner):
    for scope in ("personal", "professional", "client", "mixed"):
        assert create_context(client, owner, scope=scope).status_code == 201, scope
    assert create_context(client, owner, scope="public").status_code == 422
    assert create_context(client, owner, status="deleted").status_code == 422
    assert create_context(client, owner, status="archived").status_code == 201


def test_context_text_limits(client, owner):
    assert create_context(client, owner, slug="s" * 201).status_code == 422
    assert create_context(client, owner, name="n" * 501).status_code == 422
    assert create_context(client, owner, source="x" * 201).status_code == 422
    assert (
        create_context(client, owner, slug="s" * 200, name="n" * 500).status_code == 201
    )


def test_a_required_context_field_cannot_be_cleared(client, owner):
    context = new_context(client, owner)
    path = f"{CONTEXTS}/{context['id']}"
    for field in ("slug", "name", "context_type"):
        assert (
            client.patch(path, headers=owner, json={field: None}).status_code == 422
        ), field


def test_a_parent_context_must_exist_in_this_workspace(
    client, owner, harness, platform
):
    assert create_context(client, owner, parent_context_id=987654321).status_code == 422
    foreign = new_context(client, other_workspace(harness, platform))
    assert (
        create_context(client, owner, parent_context_id=foreign["id"]).status_code
        == 422
    )


def test_a_context_link_needs_a_project_and_a_context(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    assert (
        create_context_link(client, owner, project_id=project["id"]).status_code == 422
    )
    assert (
        create_context_link(client, owner, context_id=context["id"]).status_code == 422
    )


def test_a_context_link_must_point_at_records_that_exist(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    no_project = create_context_link(
        client, owner, project_id=987654321, context_id=context["id"]
    )
    assert no_project.status_code == 422, no_project.text
    no_context = create_context_link(
        client, owner, project_id=project["id"], context_id=987654321
    )
    assert no_context.status_code == 422, no_context.text


def test_a_context_link_cannot_point_at_records_of_another_workspace(
    client, owner, harness, platform
):
    stranger = other_workspace(harness, platform)
    foreign_project = new_project(client, stranger)
    foreign_context = new_context(client, stranger)
    project, context = new_project(client, owner), new_context(client, owner)
    wrong_project = create_context_link(
        client, owner, project_id=foreign_project["id"], context_id=context["id"]
    )
    assert wrong_project.status_code == 422, wrong_project.text
    wrong_context = create_context_link(
        client, owner, project_id=project["id"], context_id=foreign_context["id"]
    )
    assert wrong_context.status_code == 422, wrong_context.text


def test_a_context_link_weight_must_be_positive(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    ids = {"project_id": project["id"], "context_id": context["id"]}
    for weight in (0, -1, 0.00001):
        refused = create_context_link(client, owner, **ids, weight=weight)
        assert refused.status_code == 422, weight
    accepted = create_context_link(client, owner, **ids, weight=0.0001)
    assert accepted.status_code == 201, accepted.text


def test_a_context_link_weight_is_checked_on_update_too(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    link = create_context_link(
        client, owner, project_id=project["id"], context_id=context["id"]
    ).json()
    path = f"{CONTEXT_LINKS}/{link['id']}"
    assert client.patch(path, headers=owner, json={"weight": 0}).status_code == 422
    assert client.get(path, headers=owner).json()["weight"] == 1


def test_a_context_link_kind_and_source_limit(client, owner):
    project, context = new_project(client, owner), new_context(client, owner)
    ids = {"project_id": project["id"], "context_id": context["id"]}
    assert (
        create_context_link(client, owner, **ids, relation_type="owner").status_code
        == 422
    )
    assert (
        create_context_link(client, owner, **ids, source="s" * 201).status_code == 422
    )

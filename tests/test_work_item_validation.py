"""What work items and their task links refuse."""

from projects_helpers import (
    GOAL_TASK_LINKS,
    TASK_LINKS,
    WORK_ITEMS,
    create_work_item,
    new_project,
    new_work_item,
    other_workspace,
    unique,
)

LINKS = {
    "task": (TASK_LINKS, "task_id"),
    "goal task": (GOAL_TASK_LINKS, "goal_task_id"),
}


def test_a_work_item_needs_a_type_title_project_and_source_key(client, owner):
    project = new_project(client, owner)
    complete = {
        "item_type": "epic",
        "title": "Launch",
        "project_id": project["id"],
        "source_key": unique("key"),
    }
    for missing in complete:
        body = {k: v for k, v in complete.items() if k != missing}
        assert client.post(WORK_ITEMS, headers=owner, json=body).status_code == 422, (
            missing
        )


def test_item_type_must_be_epic_or_story(client, owner):
    project = new_project(client, owner)
    assert (
        create_work_item(
            client, owner, project_id=project["id"], item_type="epic"
        ).status_code
        == 201
    )
    assert (
        create_work_item(
            client, owner, project_id=project["id"], item_type="task"
        ).status_code
        == 422
    )


def test_work_item_status_must_be_a_known_state(client, owner):
    project = new_project(client, owner)
    for status in ("todo", "in_progress", "done", "blocked", "cancelled"):
        response = create_work_item(
            client, owner, project_id=project["id"], status=status
        )
        assert response.status_code == 201, status
    assert (
        create_work_item(
            client, owner, project_id=project["id"], status="open"
        ).status_code
        == 422
    )


def test_required_work_item_text_cannot_be_empty_or_cleared(client, owner):
    project = new_project(client, owner)
    assert (
        create_work_item(client, owner, project_id=project["id"], title="").status_code
        == 422
    )
    assert (
        create_work_item(
            client, owner, project_id=project["id"], source_key=""
        ).status_code
        == 422
    )
    item = new_work_item(client, owner, project_id=project["id"])
    path = f"{WORK_ITEMS}/{item['id']}"
    for field in ("item_type", "title", "project_id", "source_key"):
        assert (
            client.patch(path, headers=owner, json={field: None}).status_code == 422
        ), field


def test_work_item_text_limits(client, owner):
    project = new_project(client, owner)
    assert (
        create_work_item(
            client, owner, project_id=project["id"], title="t" * 501
        ).status_code
        == 422
    )
    assert (
        create_work_item(
            client, owner, project_id=project["id"], source_key="k" * 301
        ).status_code
        == 422
    )
    assert (
        create_work_item(
            client, owner, project_id=project["id"], source="s" * 201
        ).status_code
        == 422
    )
    ok = create_work_item(
        client, owner, project_id=project["id"], title="t" * 500, source_key="k" * 300
    )
    assert ok.status_code == 201, ok.text


def test_work_item_progress_stays_between_0_and_100(client, owner):
    project = new_project(client, owner)
    for percent, expected in ((-1, 422), (101, 422), (0, 201), (100, 201)):
        response = create_work_item(
            client, owner, project_id=project["id"], progress_percent=percent
        )
        assert response.status_code == expected, percent


def test_work_item_weight_must_be_positive(client, owner):
    project = new_project(client, owner)
    for weight, expected in ((0, 422), (-2, 422), (0.0001, 201), (3, 201)):
        response = create_work_item(
            client, owner, project_id=project["id"], weight=weight
        )
        assert response.status_code == expected, weight


def test_a_work_item_project_must_exist_in_this_workspace(
    client, owner, harness, platform
):
    assert create_work_item(client, owner, project_id=987654321).status_code == 422
    foreign = new_project(client, other_workspace(harness, platform))
    assert create_work_item(client, owner, project_id=foreign["id"]).status_code == 422


def test_a_parent_item_must_exist_in_this_workspace(client, owner, harness, platform):
    project = new_project(client, owner)
    missing = create_work_item(
        client, owner, project_id=project["id"], parent_item_id=987654321
    )
    assert missing.status_code == 422
    stranger = other_workspace(harness, platform)
    foreign = new_work_item(client, stranger)
    wrong = create_work_item(
        client, owner, project_id=project["id"], parent_item_id=foreign["id"]
    )
    assert wrong.status_code == 422


def test_goal_id_must_be_a_number(client, owner):
    project = new_project(client, owner)
    assert (
        create_work_item(
            client, owner, project_id=project["id"], goal_id="later"
        ).status_code
        == 422
    )


def test_a_task_link_needs_a_work_item_and_a_task(client, owner):
    item = new_work_item(client, owner)
    for path, id_field in LINKS.values():
        no_task = client.post(path, headers=owner, json={"work_item_id": item["id"]})
        assert no_task.status_code == 422, (path, "task")
        no_item = client.post(path, headers=owner, json={id_field: 1})
        assert no_item.status_code == 422, (path, "item")


def test_a_task_link_must_point_at_a_work_item_that_exists(
    client, owner, harness, platform
):
    foreign = new_work_item(client, other_workspace(harness, platform))
    for path, id_field in LINKS.values():
        missing = client.post(
            path, headers=owner, json={"work_item_id": 987654321, id_field: 1}
        )
        assert missing.status_code == 422, (path, missing.text)
        wrong = client.post(
            path, headers=owner, json={"work_item_id": foreign["id"], id_field: 1}
        )
        assert wrong.status_code == 422, (path, wrong.text)


def test_task_link_weight_and_kind(client, owner):
    item = new_work_item(client, owner)
    for path, id_field in LINKS.values():
        ids = {"work_item_id": item["id"], id_field: 1}
        assert (
            client.post(path, headers=owner, json={**ids, "weight": 0}).status_code
            == 422
        ), path
        assert (
            client.post(
                path, headers=owner, json={**ids, "relation_type": "blocks"}
            ).status_code
            == 422
        ), path
        ok = client.post(path, headers=owner, json={**ids, "relation_type": "supports"})
        assert ok.status_code == 201, (path, ok.text)

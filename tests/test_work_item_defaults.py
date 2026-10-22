"""Defaults and uniqueness of work items and their task links."""

from projects_helpers import (
    GOAL_TASK_LINKS,
    TASK_LINKS,
    WORK_ITEMS,
    create_work_item,
    make,
    new_project,
    new_work_item,
    unique,
)

LINKS = [(TASK_LINKS, "task_id"), (GOAL_TASK_LINKS, "goal_task_id")]


def test_new_work_item_is_a_todo_with_no_progress(client, owner):
    project = new_project(client, owner)
    response = create_work_item(client, owner, project_id=project["id"])
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["status"] == "todo"
    assert item["progress_percent"] == 0
    assert item["weight"] == 1
    assert item["source"] == "manual"
    assert item["goal_id"] is None
    assert item["parent_item_id"] is None
    assert item["version"] == 1


def test_source_key_is_unique_across_work_items(client, owner):
    project = new_project(client, owner)
    key = unique("taken")
    assert (
        create_work_item(
            client, owner, project_id=project["id"], source_key=key
        ).status_code
        == 201
    )
    other_project = new_project(client, owner)
    again = create_work_item(
        client, owner, project_id=other_project["id"], source_key=key
    )
    assert again.status_code == 409


def test_work_items_may_share_a_title(client, owner):
    project = new_project(client, owner)
    for _ in range(2):
        response = create_work_item(
            client, owner, project_id=project["id"], title="Same"
        )
        assert response.status_code == 201, response.text


def test_a_story_can_sit_under_an_epic(client, owner):
    project = new_project(client, owner)
    epic = new_work_item(client, owner, project_id=project["id"], item_type="epic")
    story = create_work_item(
        client, owner, project_id=project["id"], parent_item_id=epic["id"]
    )
    assert story.status_code == 201, story.text
    assert story.json()["parent_item_id"] == epic["id"]


def test_work_item_import_keeps_the_old_id(client, owner):
    project = new_project(client, owner)
    imported = create_work_item(client, owner, project_id=project["id"], legacy_id=9090)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 9090
    found = client.get(f"{WORK_ITEMS}/legacy/9090", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 9090
    again = create_work_item(client, owner, project_id=project["id"], legacy_id=9090)
    assert again.status_code == 409


def test_new_task_links_implement_the_item_with_full_weight(client, owner):
    item = new_work_item(client, owner)
    for path, id_field in LINKS:
        link = make(client, owner, path, work_item_id=item["id"], **{id_field: 1})
        assert link["relation_type"] == "implements", path
        assert link["weight"] == 1, path
        assert link["version"] == 1, path


def test_a_work_item_links_to_each_task_only_once(client, owner):
    item = new_work_item(client, owner)
    for path, id_field in LINKS:
        ids = {"work_item_id": item["id"], id_field: 5}
        make(client, owner, path, **ids)
        assert client.post(path, headers=owner, json=ids).status_code == 409, path
        other_task = client.post(
            path, headers=owner, json={"work_item_id": item["id"], id_field: 6}
        )
        assert other_task.status_code == 201, (path, other_task.text)


def test_a_task_can_serve_several_work_items(client, owner):
    first, second = new_work_item(client, owner), new_work_item(client, owner)
    for path, id_field in LINKS:
        for item in (first, second):
            response = client.post(
                path, headers=owner, json={"work_item_id": item["id"], id_field: 77}
            )
            assert response.status_code == 201, (path, response.text)

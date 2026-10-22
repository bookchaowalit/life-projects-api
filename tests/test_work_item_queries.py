"""Listing, grouping and the lifecycle of work items and their task links."""

import uuid

from projects_helpers import (
    GOAL_TASK_LINKS,
    TASK_LINKS,
    WORK_ITEMS,
    make,
    new_project,
    new_work_item,
)


def test_list_filters_work_items_by_type_status_goal_project_and_parent(client, owner):
    project = new_project(client, owner)
    epic = new_work_item(client, owner, project_id=project["id"], item_type="epic")
    story = new_work_item(
        client,
        owner,
        project_id=project["id"],
        item_type="story",
        status="blocked",
        goal_id=42,
        parent_item_id=epic["id"],
    )
    base = {"project_id": project["id"]}
    for params, expected in (
        ({**base, "item_type": "epic"}, [epic["id"]]),
        ({**base, "status": "blocked"}, [story["id"]]),
        ({**base, "goal_id": 42}, [story["id"]]),
        ({"parent_item_id": epic["id"]}, [story["id"]]),
        ({**base, "source_key": story["source_key"]}, [story["id"]]),
    ):
        listed = client.get(WORK_ITEMS, headers=owner, params=params)
        assert listed.status_code == 200, listed.text
        assert [i["id"] for i in listed.json()["items"]] == expected, params


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    assert (
        client.get(WORK_ITEMS, headers=owner, params={"title": "x"}).status_code == 422
    )


def test_stats_count_work_items_per_status_and_type(client, owner):
    new_work_item(client, owner, status="cancelled", item_type="epic")
    by_status = client.get(
        f"{WORK_ITEMS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert by_status.status_code == 200, by_status.text
    assert by_status.json()["groups"]["cancelled"] >= 1
    by_type = client.get(
        f"{WORK_ITEMS}/stats", headers=owner, params={"group_by": "item_type"}
    )
    assert by_type.json()["groups"]["epic"] >= 1
    refused = client.get(
        f"{WORK_ITEMS}/stats", headers=owner, params={"group_by": "title"}
    )
    assert refused.status_code == 422


def test_finishing_a_work_item_bumps_the_version_once(client, owner):
    item = new_work_item(client, owner)
    path = f"{WORK_ITEMS}/{item['id']}"
    done = client.patch(
        path, headers=owner, json={"status": "done", "progress_percent": 100}
    )
    assert done.status_code == 200, done.text
    assert done.json()["version"] == 2
    unchanged = client.patch(path, headers=owner, json={"status": "done"})
    assert unchanged.json()["version"] == 2


def test_a_work_item_can_move_to_another_project(client, owner):
    item = new_work_item(client, owner)
    target = new_project(client, owner)
    moved = client.patch(
        f"{WORK_ITEMS}/{item['id']}", headers=owner, json={"project_id": target["id"]}
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["project_id"] == target["id"]


def test_a_project_with_work_items_cannot_be_deleted(client, owner):
    project = new_project(client, owner)
    item = new_work_item(client, owner, project_id=project["id"])
    blocked = client.delete(f"/v1/projects/{project['id']}", headers=owner)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == {"error": "has_dependents"}
    assert client.delete(f"{WORK_ITEMS}/{item['id']}", headers=owner).status_code == 204
    assert (
        client.delete(f"/v1/projects/{project['id']}", headers=owner).status_code == 204
    )


def test_a_work_item_with_children_or_links_cannot_be_deleted(client, owner):
    project = new_project(client, owner)
    epic = new_work_item(client, owner, project_id=project["id"], item_type="epic")
    story = new_work_item(
        client, owner, project_id=project["id"], parent_item_id=epic["id"]
    )
    assert client.delete(f"{WORK_ITEMS}/{epic['id']}", headers=owner).status_code == 409
    link = make(client, owner, TASK_LINKS, work_item_id=story["id"], task_id=1)
    blocked = client.delete(f"{WORK_ITEMS}/{story['id']}", headers=owner)
    assert blocked.status_code == 409, blocked.text
    assert client.delete(f"{TASK_LINKS}/{link['id']}", headers=owner).status_code == 204
    assert (
        client.delete(f"{WORK_ITEMS}/{story['id']}", headers=owner).status_code == 204
    )
    assert client.delete(f"{WORK_ITEMS}/{epic['id']}", headers=owner).status_code == 204


def test_task_links_are_listed_by_item_task_and_relation(client, owner):
    first, second = new_work_item(client, owner), new_work_item(client, owner)
    task_id = uuid.uuid4().int % 10**9
    implements = make(
        client, owner, TASK_LINKS, work_item_id=first["id"], task_id=task_id
    )
    supports = make(
        client,
        owner,
        TASK_LINKS,
        work_item_id=second["id"],
        task_id=task_id,
        relation_type="supports",
    )
    by_task = client.get(TASK_LINKS, headers=owner, params={"task_id": task_id})
    assert {x["id"] for x in by_task.json()["items"]} == {
        implements["id"],
        supports["id"],
    }
    by_item = client.get(
        TASK_LINKS, headers=owner, params={"work_item_id": first["id"]}
    )
    assert [x["id"] for x in by_item.json()["items"]] == [implements["id"]]
    by_relation = client.get(
        TASK_LINKS,
        headers=owner,
        params={"task_id": task_id, "relation_type": "supports"},
    )
    assert [x["id"] for x in by_relation.json()["items"]] == [supports["id"]]


def test_goal_task_links_are_listed_by_item_and_goal_task(client, owner):
    item = new_work_item(client, owner)
    link = make(
        client, owner, GOAL_TASK_LINKS, work_item_id=item["id"], goal_task_id=314
    )
    by_item = client.get(
        GOAL_TASK_LINKS, headers=owner, params={"work_item_id": item["id"]}
    )
    assert [x["id"] for x in by_item.json()["items"]] == [link["id"]]
    by_goal_task = client.get(
        GOAL_TASK_LINKS, headers=owner, params={"goal_task_id": 314}
    )
    assert link["id"] in [x["id"] for x in by_goal_task.json()["items"]]


def test_task_link_stats_group_by_relation_and_refuse_other_fields(client, owner):
    item = new_work_item(client, owner)
    for path, id_field in ((TASK_LINKS, "task_id"), (GOAL_TASK_LINKS, "goal_task_id")):
        make(
            client,
            owner,
            path,
            work_item_id=item["id"],
            relation_type="supports",
            **{id_field: 8},
        )
        stats = client.get(
            f"{path}/stats", headers=owner, params={"group_by": "relation_type"}
        )
        assert stats.status_code == 200, stats.text
        assert stats.json()["groups"]["supports"] >= 1, path
        refused = client.get(
            f"{path}/stats", headers=owner, params={"group_by": "weight"}
        )
        assert refused.status_code == 422, path


def test_a_task_link_can_be_reweighted_and_deleted(client, owner):
    item = new_work_item(client, owner)
    link = make(client, owner, TASK_LINKS, work_item_id=item["id"], task_id=2)
    path = f"{TASK_LINKS}/{link['id']}"
    changed = client.patch(
        path, headers=owner, json={"weight": 2.5, "relation_type": "supports"}
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["weight"] == 2.5
    assert changed.json()["version"] == 2
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404

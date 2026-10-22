"""What projects and their repositories refuse."""

from projects_helpers import (
    PROJECT_REPOS,
    PROJECTS,
    create_project,
    create_repo,
    new_project,
    other_workspace,
    unique,
)

CATEGORIES = ["product", "client", "internal", "experiment", "portfolio", "open_source"]
STATUSES = [
    "idea",
    "planning",
    "active",
    "paused",
    "completed",
    "abandoned",
    "archived",
]
ROLES = [
    "frontend",
    "backend",
    "fullstack",
    "docs",
    "infra",
    "script",
    "mobile",
    "other",
]


def test_a_project_needs_a_name_and_a_slug(client, owner):
    assert (
        client.post(PROJECTS, headers=owner, json={"name": "Site"}).status_code == 422
    )
    assert (
        client.post(PROJECTS, headers=owner, json={"slug": unique("p")}).status_code
        == 422
    )


def test_required_project_text_cannot_be_empty_or_cleared(client, owner):
    assert create_project(client, owner, name="").status_code == 422
    assert create_project(client, owner, slug="").status_code == 422
    project = new_project(client, owner)
    path = f"{PROJECTS}/{project['id']}"
    for field in ("name", "slug"):
        assert (
            client.patch(path, headers=owner, json={field: None}).status_code == 422
        ), field


def test_project_text_limits(client, owner):
    assert create_project(client, owner, name="n" * 501).status_code == 422
    assert create_project(client, owner, slug="s" * 201).status_code == 422
    assert create_project(client, owner, type="t" * 101).status_code == 422
    assert create_project(client, owner, phase="p" * 201).status_code == 422
    assert create_project(client, owner, color="c" * 41).status_code == 422
    assert create_project(client, owner, domain="d" * 201).status_code == 422
    assert (
        create_project(client, owner, name="n" * 500, slug="s" * 200).status_code == 201
    )


def test_project_category_must_be_a_known_kind(client, owner):
    for category in CATEGORIES:
        assert create_project(client, owner, category=category).status_code == 201, (
            category
        )
    assert create_project(client, owner, category="hobby").status_code == 422


def test_project_status_must_be_a_known_state(client, owner):
    for status in STATUSES:
        assert create_project(client, owner, status=status).status_code == 201, status
    assert create_project(client, owner, status="done").status_code == 422


def test_progress_percent_stays_between_0_and_100(client, owner):
    assert create_project(client, owner, progress_percent=-1).status_code == 422
    assert create_project(client, owner, progress_percent=101).status_code == 422
    assert create_project(client, owner, progress_percent=0).status_code == 201
    assert create_project(client, owner, progress_percent=100).status_code == 201


def test_progress_percent_is_checked_on_update_too(client, owner):
    project = new_project(client, owner, progress_percent=40)
    path = f"{PROJECTS}/{project['id']}"
    assert (
        client.patch(path, headers=owner, json={"progress_percent": 140}).status_code
        == 422
    )
    assert client.get(path, headers=owner).json()["progress_percent"] == 40


def test_project_dates_must_be_real_dates(client, owner):
    for field in ("start_date", "target_launch", "launched_at", "completed_at"):
        assert (
            create_project(client, owner, **{field: "next year"}).status_code == 422
        ), field
        assert (
            create_project(client, owner, **{field: "2026-02-30"}).status_code == 422
        ), field
        assert (
            create_project(client, owner, **{field: "2026-03-01"}).status_code == 201
        ), field


def test_archived_at_must_be_a_timestamp(client, owner):
    assert create_project(client, owner, archived_at="whenever").status_code == 422
    ok = create_project(client, owner, archived_at="2026-10-01T10:00:00+00:00")
    assert ok.status_code == 201, ok.text


def test_counts_and_revenue_must_be_numbers(client, owner):
    assert create_project(client, owner, task_count="many").status_code == 422
    assert create_project(client, owner, completed_count=1.5).status_code == 422
    assert create_project(client, owner, monthly_revenue="lots").status_code == 422
    assert create_project(client, owner, total_revenue="lots").status_code == 422


def test_a_parent_project_must_exist(client, owner):
    assert create_project(client, owner, parent_project_id=987654321).status_code == 422
    assert create_project(client, owner, parent_project_id=0).status_code == 422


def test_a_parent_project_cannot_be_from_another_workspace(
    client, owner, harness, platform
):
    foreign = new_project(client, other_workspace(harness, platform))
    assert (
        create_project(client, owner, parent_project_id=foreign["id"]).status_code
        == 422
    )


def test_a_repository_needs_a_name(client, owner):
    assert client.post(PROJECT_REPOS, headers=owner, json={}).status_code == 422
    assert create_repo(client, owner, repo_name="").status_code == 422


def test_repository_text_limits(client, owner):
    assert create_repo(client, owner, repo_name="r" * 301).status_code == 422
    assert create_repo(client, owner, language="l" * 101).status_code == 422
    assert (
        create_repo(client, owner, repo_name="r" * 300, language="l" * 100).status_code
        == 201
    )


def test_repository_role_must_be_a_known_kind(client, owner):
    for role in ROLES:
        assert create_repo(client, owner, role=role).status_code == 201, role
    assert create_repo(client, owner, role="database").status_code == 422


def test_is_primary_must_be_true_or_false(client, owner):
    assert create_repo(client, owner, is_primary="sort of").status_code == 422
    assert create_repo(client, owner, is_primary=True).status_code == 201


def test_a_repository_project_must_exist_in_this_workspace(
    client, owner, harness, platform
):
    assert create_repo(client, owner, project_id=987654321).status_code == 422
    foreign = new_project(client, other_workspace(harness, platform))
    assert create_repo(client, owner, project_id=foreign["id"]).status_code == 422

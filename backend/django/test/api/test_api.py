from test.util import compare_get_response, read_test_data_api

import pytest

from core.management.commands.seed import (
    SEED_EMAIL,
    SEED_LABELS,
    SEED_PASSWORD,
    SEED_PASSWORD2,
    SEED_PROJECT,
    SEED_USERNAME,
    SEED_USERNAME2,
)
from core.models import Profile, ProjectPermissions
from core.pagination import SmartPagination
from core.utils.utils_queue import fill_queue


def test_get_projects(seeded_database, admin_client):
    response = admin_client.get("/api/projects/")
    compare_get_response(response, [{"name": SEED_PROJECT}], ["name"])


@pytest.mark.skip(
    reason="Currently failing with FAILED test/api/test_api.py::test_get_users - django.core.exceptions.ImproperlyConfigured"
)
def test_get_users(seeded_database, admin_client):
    response = admin_client.get("/api/users/")
    compare_get_response(response, [{}], [])


@pytest.mark.skip(
    reason="Currently failing with FAILED test/api/test_api.py::test_get_auth_users - django.core.exceptions.ImproperlyConfigured"
)
def test_get_auth_users(seeded_database, admin_client):
    response = admin_client.get("/api/auth_users/")
    compare_get_response(
        response,
        [
            {"username": SEED_USERNAME, "email": SEED_EMAIL},
            {"username": SEED_USERNAME2, "email": SEED_EMAIL},
            # Special user created for the admin_client to run tests
            {"username": "admin", "email": "admin@example.com"},
        ],
        ["username", "email"],
    )


def test_login(seeded_database, client, db):
    assert client.login(username=SEED_USERNAME, password=SEED_PASSWORD)


def test_get_labels(seeded_database, admin_client):
    response = admin_client.get("/api/labels/")
    compare_get_response(response, [{"name": label} for label in SEED_LABELS], ["name"])


def test_get_data(seeded_database, admin_client):
    expected = read_test_data_api()
    expected = [{"text": x["Text"]} for x in expected]

    assert SmartPagination.max_page_size >= len(expected), (
        "SmartPagination's max_page_size setting must be larger than the "
        "size of the sample dataset for this test to run properly."
    )

    response = admin_client.get("/api/data/?page_size={}".format(len(expected)))
    compare_get_response(response, expected, ["text"])


def test_queue_refills_after_empty(
    seeded_database,
    client,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_labels_half_irr,
):
    """This tests that the queue refills when it should."""

    # sign in users
    labels = test_labels_half_irr
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    project = test_project_half_irr_data

    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)
    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )

    # get the card deck
    response = client.get("/api/get_card_deck/" + str(project.pk) + "/").json()
    assert len(response["data"]) > 0
    # label all of the cards
    i = 0
    for card in response["data"]:
        response = client.post(
            "/api/annotate_data/" + str(card["pk"]) + "/",
            {"labelID": labels[i % 3].pk, "labeling_time": 3},
        )
        i += 1

    # get the card deck again
    response = client.get("/api/get_card_deck/" + str(project.pk) + "/").json()

    # should have cards
    assert len(response["data"]) > 0


def test_download_model(
    seeded_database,
    client,
    admin_client,
    test_project_with_trained_model,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_admin_queue_labeled,
):
    """This tests the download model api call."""
    project = test_project_with_trained_model
    fill_queue(
        test_queue_labeled,
        "random",
        test_irr_queue_labeled,
        project.percentage_irr,
        project.batch_size,
    )

    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    admin_profile = Profile.objects.get(user__username=SEED_USERNAME2)
    ProjectPermissions.objects.create(
        profile=admin_profile, project=project, permission="ADMIN"
    )

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)

    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )

    # check admin priviledges
    response = client.get("/api/download_model/" + str(project.pk) + "/").json()
    assert (
        "detail" in response
        and "Invalid permission. Must be an admin" in response["detail"]
    )

    # check that the response is the correct type
    response = admin_client.get("/api/download_model/" + str(project.pk) + "/")
    assert "detail" not in response
    assert response.get("Content-Type") == "application/x-zip-compressed"


def test_download_labeled_data(
    seeded_database,
    client,
    admin_client,
    test_project_labeled,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_admin_queue_labeled,
):
    """This tests the download labeled data api call."""
    project = test_project_labeled
    fill_queue(
        test_queue_labeled,
        "random",
        test_irr_queue_labeled,
        project.percentage_irr,
        project.batch_size,
    )

    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    admin_profile = Profile.objects.get(user__username=SEED_USERNAME2)
    ProjectPermissions.objects.create(
        profile=admin_profile, project=project, permission="ADMIN"
    )

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)

    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )
    # check admin priviledges
    response = client.get("/api/download_data/" + str(project.pk) + "/").json()
    assert (
        "detail" in response
        and "Invalid permission. Must be an admin" in response["detail"]
    )

    # check that the response is the correct type
    response = admin_client.get("/api/download_data/" + str(project.pk) + "/")
    assert "detail" not in response
    assert response.get("Content-Type") == "text/csv"

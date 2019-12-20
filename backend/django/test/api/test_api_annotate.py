from test.util import assert_collections_equal, sign_in_and_fill_queue

from core.management.commands.seed import (
    SEED_PASSWORD,
    SEED_PASSWORD2,
    SEED_USERNAME,
    SEED_USERNAME2,
)
from core.models import (
    AssignedData,
    Data,
    DataLabel,
    DataQueue,
    IRRLog,
    LabelChangeLog,
    Profile,
    ProjectPermissions,
    RecycleBin,
)
from core.utils.utils_annotate import get_assignments
from core.utils.utils_queue import fill_queue


def test_get_label_history(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_labels,
    test_admin_queue,
    test_irr_queue,
):
    """This tests the function that returns the elements that user has already
    labeled."""
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )
    # before anything has been labeled, the history table should be empty
    response = admin_client.get("/api/get_label_history/" + str(project.pk) + "/")
    assert response.json()["data"] == []

    # skip an item. Should still be empty
    data = get_assignments(client_profile, project, 2)
    datum = data[0]
    assert datum is not None
    response = client.post("/api/skip_data/" + str(datum.pk) + "/")
    assert "error" not in response.json() and "detail" not in response.json()

    response = client.get("/api/get_label_history/" + str(project.pk) + "/")
    assert response.json()["data"] == []

    # have one user label something. Call label history on two users.
    request_info = {"labelID": test_labels[0].pk, "labeling_time": 3}
    datum = data[1]
    response = client.post("/api/annotate_data/" + str(datum.pk) + "/", request_info)
    assert "error" not in response.json() and "detail" not in response.json()

    response_client = client.get("/api/get_label_history/" + str(project.pk) + "/")
    assert response_client.json()["data"] != []

    response_admin = admin_client.get("/api/get_label_history/" + str(project.pk) + "/")
    assert response_admin.json()["data"] == []

    # the label should be in the correct person's history
    response_data = response_client.json()["data"][0]
    assert response_data["id"] == datum.pk
    assert response_data["labelID"] == test_labels[0].pk


def test_annotate_data(
    seeded_database,
    client,
    test_project_data,
    test_queue,
    test_labels,
    test_admin_queue,
    test_irr_queue,
):
    """This tests the basic ability to annotate a datum."""
    # get a datum from the queue
    project = test_project_data
    fill_queue(test_queue, "random")
    request_info = {"labelID": test_labels[0].pk, "labeling_time": 3}
    permission_message = (
        "Account disabled by administrator.  Please contact project owner for details"
    )
    # call annotate data without the user having permission. Check that
    # the data is not annotated and the response has an error.
    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)

    data = get_assignments(client_profile, project, 1)
    response = client.post("/api/annotate_data/" + str(data[0].pk) + "/", request_info)
    assert (
        "detail" in response.json() and permission_message in response.json()["detail"]
    )

    assert DataLabel.objects.filter(data=data[0]).count() == 0
    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )

    # give the user permission and call annotate again
    # The data should be labeled and in the proper places
    # check that the response was {} (no error)
    response = client.post("/api/annotate_data/" + str(data[0].pk) + "/", request_info)
    assert "error" not in response.json() and "detail" not in response.json()
    assert DataLabel.objects.filter(data=data[0]).count() == 1
    assert DataQueue.objects.filter(data=data[0]).count() == 0


def test_skip_data(
    seeded_database,
    client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
):
    """This tests that the skip data api works."""
    project = test_project_data
    fill_queue(test_queue, "random")
    permission_message = (
        "Account disabled by administrator.  Please contact project owner for details"
    )
    # call skip data without the user having permission. Check that
    # the data is not in admin and the response has an error.
    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)

    data = get_assignments(client_profile, project, 1)
    response = client.post("/api/skip_data/" + str(data[0].pk) + "/")
    assert (
        "detail" in response.json() and permission_message in response.json()["detail"]
    )

    assert DataQueue.objects.filter(data=data[0], queue=test_queue).count() == 1
    assert DataQueue.objects.filter(data=data[0], queue=test_admin_queue).count() == 0
    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )

    # have someone skip something with permission. Should
    # be in admin queue, not in normal queue, not in datalabel
    response = client.post("/api/skip_data/" + str(data[0].pk) + "/")
    assert "error" not in response.json() and "detail" not in response.json()

    assert DataQueue.objects.filter(data=data[0], queue=test_queue).count() == 0
    assert DataQueue.objects.filter(data=data[0], queue=test_admin_queue).count() == 1
    assert DataLabel.objects.filter(data=data[0]).count() == 0


def test_modify_label(
    seeded_database,
    client,
    test_project_data,
    test_queue,
    test_labels,
    test_irr_queue,
    test_admin_queue,
):
    """This tests the history table's ability to modify a label."""
    request_info = {"labelID": test_labels[0].pk, "labeling_time": 3}
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(project, test_queue, client)
    # have a user annotate some data
    data = get_assignments(client_profile, project, 1)[0]
    assert data is not None
    response = client.post("/api/annotate_data/" + str(data.pk) + "/", request_info)
    assert DataLabel.objects.filter(data=data).count() == 1

    # call modify label to change it to something else
    change_info = {
        "dataID": data.pk,
        "oldLabelID": test_labels[0].pk,
        "labelID": test_labels[1].pk,
    }
    response = client.post("/api/modify_label/" + str(data.pk) + "/", change_info)
    assert "error" not in response.json() and "detail" not in response.json()
    # check that the label is updated and it's in the correct places
    # check that there are no duplicate labels
    assert DataLabel.objects.filter(data=data).count() == 1
    assert DataLabel.objects.get(data=data).label.pk == test_labels[1].pk
    # check it's in change log
    assert LabelChangeLog.objects.filter(data=data).count() == 1


def test_modify_label_to_skip(
    seeded_database,
    client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
):
    """This tests the history table's ability to change labeled items to skipped
    items."""
    request_info = {"labelID": test_labels[0].pk, "labeling_time": 3}
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(project, test_queue, client)
    # have a user annotate some data
    data = get_assignments(client_profile, project, 1)[0]
    assert data is not None
    response = client.post("/api/annotate_data/" + str(data.pk) + "/", request_info)
    assert DataLabel.objects.filter(data=data).count() == 1

    # Call the change to skip function. Should now be in admin table, not be
    # in history table.
    change_info = {"dataID": data.pk, "oldLabelID": test_labels[0].pk}
    response = client.post(
        "/api/modify_label_to_skip/" + str(data.pk) + "/", change_info
    )
    assert "error" not in response.json() and "detail" not in response.json()

    assert DataLabel.objects.filter(data=data).count() == 0
    assert DataQueue.objects.filter(queue=test_admin_queue).count() == 1
    # check it's in change log
    assert LabelChangeLog.objects.filter(data=data, new_label="skip").count() == 1


def test_skew_label(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_labels,
    test_irr_queue,
    test_admin_queue,
):
    """This tests the skew label functionalty, which takes unlabeled and unnasigned data
    and labels it."""
    request_info = {"labelID": test_labels[0].pk, "labeling_time": 3}
    project = test_project_data
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

    # have a regular coder try and label things. Should not be allowed.
    data = Data.objects.filter(project=project)[0]
    assert data is not None
    response = client.post("/api/label_skew_label/" + str(data.pk) + "/", request_info)
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )
    # have an admin try and label. Should be allowed.
    response = admin_client.post(
        "/api/label_skew_label/" + str(data.pk) + "/", request_info
    )
    assert "error" not in response.json() and "detail" not in response.json()
    assert DataLabel.objects.filter(data=data).count() == 1


def test_skip_data_api(
    seeded_database,
    client,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_labels_half_irr,
):
    """This tests that skipping works properly from the api side."""
    # sign in users
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

    # for each card in the deck, skip it
    for card in response["data"]:
        response = client.post("/api/skip_data/" + str(card["pk"]) + "/")
        if card["irr_ind"]:
            # if it was irr data, check that it is not in admin queue
            assert (
                DataQueue.objects.filter(data__pk=card["pk"], queue=admin_queue).count()
                == 0
            )
            assert (
                DataQueue.objects.filter(data__pk=card["pk"], queue=irr_queue).count()
                == 1
            )
            assert (
                AssignedData.objects.filter(
                    data__pk=card["pk"], profile=client_profile
                ).count()
                == 0
            )
        else:
            # if it is not irr data, check that it is in admin queue
            assert (
                DataQueue.objects.filter(data__pk=card["pk"], queue=admin_queue).count()
                == 1
            )
            assert (
                DataQueue.objects.filter(data__pk=card["pk"], queue=irr_queue).count()
                == 0
            )
            assert (
                AssignedData.objects.filter(
                    data__pk=card["pk"], profile=client_profile
                ).count()
                == 0
            )


def test_admin_label(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_labels,
    test_irr_queue,
    test_admin_queue,
):
    """This tests the admin ability to label skipped items in the admin table."""
    # fill queue. The admin queue should be empty
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )
    assert DataQueue.objects.filter(queue=test_admin_queue).count() == 0
    # have a normal client skip something and try to admin label. Should not
    # be allowed
    data = get_assignments(client_profile, project, 1)[0]
    response = client.post("/api/skip_data/" + str(data.pk) + "/")
    assert "error" not in response.json() and "detail" not in response.json()

    payload = {"labelID": test_labels[0].pk}
    response = client.post("/api/label_admin_label/" + str(data.pk) + "/", payload)

    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )

    # check datum is in proper places
    assert DataQueue.objects.filter(data=data, queue=test_admin_queue).count() == 1
    assert DataQueue.objects.filter(data=data, queue=test_queue).count() == 0
    assert DataLabel.objects.filter(data=data).count() == 0

    # Let admin label datum. Should work. Check it is now in proper places
    response = admin_client.post(
        "/api/label_admin_label/" + str(data.pk) + "/", payload
    )
    assert "error" not in response.json() and "detail" not in response.json()
    assert DataQueue.objects.filter(data=data, queue=test_admin_queue).count() == 0
    assert DataLabel.objects.filter(data=data).count() == 1


def test_label_distribution_inverted(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
):
    """This tests the api that produces the label counts chart for the skew page.

    It is stacked differently than the previous.
    """
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )

    # at the beginning, should return empty list
    response = client.get("/api/label_distribution/" + str(project.pk) + "/")
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )

    response = admin_client.get("/api/label_distribution/" + str(project.pk) + "/")
    assert len(response.json()) == 0

    # have client label three things differently. Check values.
    data = get_assignments(client_profile, project, 3)
    response = client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 3},
    )
    response = client.post(
        "/api/annotate_data/" + str(data[1].pk) + "/",
        {"labelID": test_labels[1].pk, "labeling_time": 3},
    )
    response = client.post(
        "/api/annotate_data/" + str(data[2].pk) + "/",
        {"labelID": test_labels[2].pk, "labeling_time": 3},
    )
    assert DataLabel.objects.filter(data__in=data).count() == 3

    response = admin_client.get(
        "/api/label_distribution_inverted/" + str(project.pk) + "/"
    ).json()
    assert len(response) > 0

    for row in response:
        user = row["key"]
        temp_dict = row["values"]
        for label_row in temp_dict:
            if user == str(client_profile):
                assert label_row["y"] == 1
            else:
                assert user in [str(admin_profile), "test_profile"]
                assert label_row["y"] == 0

    # Have admin label three things the same. Check values.
    data = get_assignments(admin_profile, project, 3)
    response = admin_client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 3},
    )
    response = admin_client.post(
        "/api/annotate_data/" + str(data[1].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 3},
    )
    response = admin_client.post(
        "/api/annotate_data/" + str(data[2].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 3},
    )

    response = admin_client.get(
        "/api/label_distribution_inverted/" + str(project.pk) + "/"
    ).json()
    assert len(response) > 0

    for row in response:
        user = row["key"]
        temp_dict = row["values"]
        for label_row in temp_dict:
            if user == str(client_profile):
                assert label_row["y"] == 1
            elif user == str(admin_profile):
                if label_row["x"] == test_labels[0].name:
                    assert label_row["y"] == 3
                else:
                    assert label_row["y"] == 0
            else:
                assert label_row["y"] == 0


def test_unlabeled_table(
    seeded_database,
    client,
    admin_client,
    test_project_unlabeled_and_tfidf,
    test_queue,
    test_admin_queue,
    test_irr_queue,
    test_labels,
):
    """This tests that the unlabeled data table contains what it should."""
    project = test_project_unlabeled_and_tfidf
    # first, check that it has all the unlabeled data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )
    response = client.get("/api/data_unlabeled_table/" + str(project.pk) + "/")
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )

    response = admin_client.get(
        "/api/data_unlabeled_table/" + str(project.pk) + "/"
    ).json()
    assert "data" in response
    assert (
        len(response["data"])
        == Data.objects.filter(project=project).count()
        - DataQueue.objects.filter(data__project=project).count()
    )

    # label something. Check it is not in the table.
    data = get_assignments(client_profile, project, 2)
    response = client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 1},
    )
    response = admin_client.get(
        "/api/data_unlabeled_table/" + str(project.pk) + "/"
    ).json()
    data_ids = [d["ID"] for d in response["data"]]
    assert data[0].pk not in data_ids

    # skip something. Check it is not in the table.
    response = client.post("/api/skip_data/" + str(data[1].pk) + "/")
    response = admin_client.get(
        "/api/data_unlabeled_table/" + str(project.pk) + "/"
    ).json()
    data_ids = [d["ID"] for d in response["data"]]
    assert data[1].pk not in data_ids


def test_admin_table(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_admin_queue,
    test_labels,
):
    """This tests that the admin table holds the correct items."""
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )
    # check that a non-admin can't get the table
    response = client.get("/api/data_admin_table/" + str(project.pk) + "/").json()
    assert (
        "detail" in response
        and "Invalid permission. Must be an admin" in response["detail"]
    )

    response = admin_client.get("/api/data_admin_table/" + str(project.pk) + "/").json()
    # first, check that it is empty
    assert len(response["data"]) == 0

    # label something. Should still be empty.
    data = get_assignments(client_profile, project, 2)
    response = client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 1},
    )
    response = admin_client.get("/api/data_admin_table/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 0

    # skip something. Should be in the table.
    response = client.post("/api/skip_data/" + str(data[1].pk) + "/")
    response = admin_client.get("/api/data_admin_table/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 1
    assert response["data"][0]["ID"] == data[1].pk

    # admin annotate the data. Admin table should be empty again.
    response = admin_client.post(
        "/api/label_admin_label/" + str(data[1].pk) + "/",
        {"labelID": test_labels[0].pk},
    )
    response = admin_client.get("/api/data_admin_table/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 0


def test_multiple_admin_on_admin_annotation(
    seeded_database,
    client,
    admin_client,
    test_project_all_irr_data,
    test_all_irr_all_queues,
    test_labels_all_irr,
):
    """This tests the functions that prevent the race condition of multiple admin
    editing any of the three admin-only tables by only allowing one admin at a time to
    view them."""
    normal_queue, admin_queue, irr_queue = test_all_irr_all_queues
    project = test_project_all_irr_data

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    a1_prof = Profile.objects.get(user__username=SEED_USERNAME)
    ProjectPermissions.objects.create(
        profile=a1_prof, project=project, permission="ADMIN"
    )
    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    a2_prof = Profile.objects.get(user__username=SEED_USERNAME2)
    ProjectPermissions.objects.create(
        profile=a2_prof, project=project, permission="ADMIN"
    )

    # first, have both admin sign in and enter the page
    response = client.get("/api/enter_coding_page/" + str(project.pk) + "/").json()
    response2 = admin_client.get(
        "/api/enter_coding_page/" + str(project.pk) + "/"
    ).json()

    assert "error" not in response and "error" not in response2

    # the first admin should have permission to view, the second should not
    response = client.get(
        "/api/check_admin_in_progress/" + str(project.pk) + "/"
    ).json()
    response2 = admin_client.get(
        "/api/check_admin_in_progress/" + str(project.pk) + "/"
    ).json()

    assert response["available"] == 1
    assert response2["available"] == 0

    # have the first admin leave the page, and the second leave then enter
    response = client.get("/api/leave_coding_page/" + str(project.pk) + "/").json()

    response2 = admin_client.get(
        "/api/leave_coding_page/" + str(project.pk) + "/"
    ).json()
    response2 = admin_client.get(
        "/api/enter_coding_page/" + str(project.pk) + "/"
    ).json()

    # the second should now have permission to see the page
    response2 = admin_client.get(
        "/api/check_admin_in_progress/" + str(project.pk) + "/"
    ).json()
    assert response2["available"] == 1

    # have the first admin enter again. They should not be able to see the page
    response = client.get("/api/enter_coding_page/" + str(project.pk) + "/").json()
    response = client.get(
        "/api/check_admin_in_progress/" + str(project.pk) + "/"
    ).json()
    assert response["available"] == 0


def test_discard_data(
    seeded_database,
    client,
    admin_client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
):
    """This tests that data can be discarded."""
    project = test_project_data
    fill_queue(
        test_queue, "random", test_irr_queue, project.percentage_irr, project.batch_size
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

    # assign a batch of data. Should be IRR and non-IRR
    data = get_assignments(client_profile, project, 30)
    assert not all(not datum.irr_ind for datum in data)
    assert not all(datum.irr_ind for datum in data)

    # call skip data on a full batch of data
    for i in range(30):
        response = client.post("/api/skip_data/" + str(data[i].pk) + "/")

    # have the admin also get a batch and call skip on everything
    data = get_assignments(admin_profile, project, 30)
    assert not all(not datum.irr_ind for datum in data)
    assert not all(datum.irr_ind for datum in data)

    # call skip data on a full batch of data
    for i in range(30):
        response = admin_client.post("/api/skip_data/" + str(data[i].pk) + "/")

    admin_data = DataQueue.objects.filter(data__project=project, queue=test_admin_queue)
    assert not all(not datum.data.irr_ind for datum in admin_data)
    assert not all(datum.data.irr_ind for datum in admin_data)

    # check for admin privalidges
    response = client.post(
        "/api/discard_data/" + str(admin_data[0].data.pk) + "/"
    ).json()
    assert (
        "detail" in response
        and "Invalid permission. Must be an admin" in response["detail"]
    )

    # get irr data and discard it. Check that the data is not in IRRLog, AssignedData DataQueue, in RecycleBin
    irr_data = admin_data.filter(data__irr_ind=True)
    for datum in irr_data:
        assert IRRLog.objects.filter(data=datum.data).count() > 0
        admin_client.post("/api/discard_data/" + str(datum.data.pk) + "/")
        assert IRRLog.objects.filter(data=datum.data).count() == 0
        assert DataQueue.objects.filter(data=datum.data).count() == 0
        assert AssignedData.objects.filter(data=datum.data).count() == 0
        assert RecycleBin.objects.filter(data=datum.data).count() == 1
        assert not RecycleBin.objects.get(data=datum.data).data.irr_ind

    # get normal data and discard it. Check that the data is not in IRRLog, AssignedData DataQueue, in RecycleBin
    non_irr_data = admin_data.filter(data__irr_ind=False)
    for datum in non_irr_data:
        admin_client.post("/api/discard_data/" + str(datum.data.pk) + "/")
        assert DataQueue.objects.filter(data=datum.data).count() == 0
        assert AssignedData.objects.filter(data=datum.data).count() == 0
        assert RecycleBin.objects.filter(data=datum.data).count() == 1


def test_restore_data(
    seeded_database,
    client,
    admin_client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
):
    """This tests that data can be restored after it is discarded."""
    project = test_project_data
    fill_queue(
        test_queue, "random", test_irr_queue, project.percentage_irr, project.batch_size
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

    # assign a batch of data. Should be IRR and non-IRR
    data = get_assignments(client_profile, project, 30)
    for i in range(30):
        response = client.post("/api/skip_data/" + str(data[i].pk) + "/")

    # have the admin also get a batch and call skip on everything
    data = get_assignments(admin_profile, project, 30)
    for i in range(30):
        response = admin_client.post("/api/skip_data/" + str(data[i].pk) + "/")

    admin_data = DataQueue.objects.filter(data__project=project, queue=test_admin_queue)
    # discard all data
    for datum in admin_data:
        admin_client.post("/api/discard_data/" + str(datum.data.pk) + "/")

    # check for admin privalidges
    response = client.post(
        "/api/restore_data/" + str(admin_data[0].data.pk) + "/"
    ).json()
    assert (
        "detail" in response
        and "Invalid permission. Must be an admin" in response["detail"]
    )

    # restore all data. It should not be in recycle bin
    for datum in admin_data:
        admin_client.post("/api/restore_data/" + str(datum.data.pk) + "/")
        assert RecycleBin.objects.filter(data=datum.data).count() == 0
        assert not Data.objects.get(pk=datum.data.pk).irr_ind


def test_recycle_bin_table(
    seeded_database,
    client,
    admin_client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
):
    """This tests that the recycle bin table is populated correctly."""
    project = test_project_data
    fill_queue(
        test_queue, "random", test_irr_queue, project.percentage_irr, project.batch_size
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

    # check for admin privalidges
    response = client.get("/api/recycle_bin_table/" + str(project.pk) + "/").json()
    assert (
        "detail" in response
        and "Invalid permission. Must be an admin" in response["detail"]
    )

    # check that the table is currently empty
    response = admin_client.get(
        "/api/recycle_bin_table/" + str(project.pk) + "/"
    ).json()
    assert "detail" not in response
    assert len(response["data"]) == 0

    # assign a batch of data. Should be IRR and non-IRR
    irr_count = 0
    non_irr_count = 0
    data = get_assignments(client_profile, project, 30)
    for i in range(30):
        if data[i].irr_ind:
            irr_count += 1
        else:
            non_irr_count += 1
        response = client.post("/api/skip_data/" + str(data[i].pk) + "/")

    # have the admin also get a batch and call skip on everything
    data = get_assignments(admin_profile, project, 30)
    for i in range(30):
        if not data[i].irr_ind:
            non_irr_count += 1
        response = admin_client.post("/api/skip_data/" + str(data[i].pk) + "/")

    admin_data = DataQueue.objects.filter(data__project=project, queue=test_admin_queue)
    # discard all data
    for datum in admin_data:
        admin_client.post("/api/discard_data/" + str(datum.data.pk) + "/")

    # check that the table has 30 elements that match the discarded data
    response = admin_client.get(
        "/api/recycle_bin_table/" + str(project.pk) + "/"
    ).json()
    assert "detail" not in response
    assert len(response["data"]) == non_irr_count + irr_count
    assert_collections_equal(
        [d["ID"] for d in response["data"]],
        RecycleBin.objects.filter(data__project=project).values_list(
            "data__pk", flat=True
        ),
    )

    # restore all data
    for datum in admin_data:
        admin_client.post("/api/restore_data/" + str(datum.data.pk) + "/")

    # check that the table is empty again
    response = admin_client.get(
        "/api/recycle_bin_table/" + str(project.pk) + "/"
    ).json()
    assert "detail" not in response
    assert len(response["data"]) == 0


def test_admin_counts(
    seeded_database,
    client,
    admin_client,
    test_project_data,
    test_queue,
    test_irr_queue,
    test_labels,
    test_admin_queue,
    test_project_no_irr_data,
    test_no_irr_all_queues,
    test_labels_no_irr,
):
    """This tests the admin counts api."""
    projects = [test_project_data, test_project_no_irr_data]
    normal_queues = [test_queue, test_no_irr_all_queues[0]]
    irr_queues = [test_irr_queue, test_no_irr_all_queues[2]]

    # log in the users into both projects
    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)
    admin_profile = Profile.objects.get(user__username=SEED_USERNAME2)
    for i in range(2):
        fill_queue(
            normal_queues[i],
            "random",
            irr_queues[i],
            projects[i].percentage_irr,
            projects[i].batch_size,
        )
        ProjectPermissions.objects.create(
            profile=admin_profile, project=projects[i], permission="ADMIN"
        )
        ProjectPermissions.objects.create(
            profile=client_profile, project=projects[i], permission="CODER"
        )
        # check for admin priviledges
        response = client.get(
            "/api/data_admin_counts/" + str(projects[i].pk) + "/"
        ).json()
        assert (
            "detail" in response
            and "Invalid permission. Must be an admin" in response["detail"]
        )

    # counts should be 0 for both projects. IRR project should have two counts.
    response = admin_client.get(
        "/api/data_admin_counts/" + str(projects[0].pk) + "/"
    ).json()
    assert "detail" not in response and len(response["data"]) == 2
    assert list(response["data"].values()) == [0, 0]

    response = admin_client.get(
        "/api/data_admin_counts/" + str(projects[1].pk) + "/"
    ).json()
    assert "detail" not in response and len(response["data"]) == 1
    assert list(response["data"].values()) == [0]

    # have admin and non_admin skip everything. The count should be 30 for non-irr project
    irr_count = 0
    non_irr_count = 0
    data = get_assignments(client_profile, projects[0], 30)
    for i in range(30):
        if data[i].irr_ind:
            irr_count += 1
        else:
            non_irr_count += 1
        response = client.post("/api/skip_data/" + str(data[i].pk) + "/")
    data = get_assignments(admin_profile, projects[0], 30)
    for i in range(30):
        if not data[i].irr_ind:
            non_irr_count += 1
        response = admin_client.post("/api/skip_data/" + str(data[i].pk) + "/")

    response = admin_client.get(
        "/api/data_admin_counts/" + str(projects[0].pk) + "/"
    ).json()
    assert "detail" not in response and len(response["data"]) == 2
    assert response["data"]["IRR"] == irr_count
    assert response["data"]["SKIP"] == non_irr_count

    # the counts should be split with the non-irr project
    data = get_assignments(client_profile, projects[1], 30)
    for i in range(30):
        response = client.post("/api/skip_data/" + str(data[i].pk) + "/")
    data = get_assignments(admin_profile, projects[1], 30)
    for i in range(30):
        response = admin_client.post("/api/skip_data/" + str(data[i].pk) + "/")

    response = admin_client.get(
        "/api/data_admin_counts/" + str(projects[1].pk) + "/"
    ).json()
    assert "detail" not in response and len(response["data"]) == 1
    assert response["data"]["SKIP"] == 60

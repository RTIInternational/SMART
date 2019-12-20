from test.util import assert_collections_equal, sign_in_and_fill_queue

import pandas as pd
from django.utils.html import escape

from core.management.commands.seed import (
    SEED_PASSWORD,
    SEED_PASSWORD2,
    SEED_USERNAME,
    SEED_USERNAME2,
)
from core.models import (
    Data,
    DataLabel,
    DataPrediction,
    Model,
    Profile,
    ProjectPermissions,
    TrainingSet,
)
from core.utils.utils_annotate import get_assignments
from core.utils.utils_queue import fill_queue


def test_get_irr_metrics(
    seeded_database,
    client,
    admin_client,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_labels_half_irr,
):
    """This tests the irr metrics api call.

    Note: the exact values are checked in the util tests.
    """

    # sign in users
    labels = test_labels_half_irr
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    project = test_project_half_irr_data

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)
    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )
    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    admin_profile = Profile.objects.get(user__username=SEED_USERNAME2)
    ProjectPermissions.objects.create(
        profile=admin_profile, project=project, permission="ADMIN"
    )

    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # non-admin should not be able to call the test
    response = client.get("/api/get_irr_metrics/" + str(project.pk) + "/")
    assert (
        403 == response.status_code
        and "Invalid permission. Must be an admin" in str(response.content)
    )

    # initially, should have no irr data processed
    response = admin_client.get("/api/get_irr_metrics/" + str(project.pk) + "/").json()
    assert "error" not in response and "detail" not in response
    assert "kappa" in response and response["kappa"] == "No irr data processed"
    assert (
        "percent agreement" in response
        and response["percent agreement"] == "No irr data processed"
    )

    # have each person label three irr data
    data = get_assignments(client_profile, project, 3)
    data2 = get_assignments(admin_profile, project, 3)
    for i in range(3):
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": labels[i].pk, "labeling_time": 3},
        )
        assert "error" not in response.json() and "detail" not in response.json()
        response = admin_client.post(
            "/api/annotate_data/" + str(data2[i].pk) + "/",
            {"labelID": labels[(i + 1) % 3].pk, "labeling_time": 3},
        )
        assert "error" not in response.json()

    response = admin_client.get("/api/get_irr_metrics/" + str(project.pk) + "/").json()
    # the percent agreement should be a number between 0 and 100 with a %
    assert "percent agreement" in response
    percent = float(
        response["percent agreement"][: len(response["percent agreement"]) - 1]
    )
    assert percent <= 100 and percent >= 0 and "%" == response["percent agreement"][-1]
    # kappa should be a value between -1 and 1
    assert "kappa" in response and response["kappa"] >= -1 and response["kappa"] <= 1


def test_percent_agree_table(
    seeded_database,
    client,
    admin_client,
    test_project_all_irr_data,
    test_all_irr_all_queues,
    test_labels_all_irr,
):
    """This tests that the percent agree table can be called and returns correctly.

    Note: the exact values of the table are checked in the util tests.
    """
    labels = test_labels_all_irr
    normal_queue, admin_queue, irr_queue = test_all_irr_all_queues
    project = test_project_all_irr_data

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)
    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )
    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    admin_profile = Profile.objects.get(user__username=SEED_USERNAME2)
    ProjectPermissions.objects.create(
        profile=admin_profile, project=project, permission="ADMIN"
    )
    third_profile = Profile.objects.get(user__username="test_profile")
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # non-admin should not be able to call the test
    response = client.get("/api/perc_agree_table/" + str(project.pk) + "/")
    assert (
        403 == response.status_code
        and "Invalid permission. Must be an admin" in str(response.content)
    )

    data = get_assignments(client_profile, project, 15)
    data2 = get_assignments(admin_profile, project, 15)
    for i in range(15):
        response = admin_client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": labels[i % 3].pk, "labeling_time": 3},
        )
        assert "error" not in response.json() and "detail" not in response.json()
        response = client.post(
            "/api/annotate_data/" + str(data2[i].pk) + "/",
            {"labelID": labels[i % 3].pk, "labeling_time": 3},
        )
        assert "error" not in response.json() and "detail" not in response.json()
    # check that the three user pairs are in table
    response = admin_client.get("/api/perc_agree_table/" + str(project.pk) + "/").json()
    assert "data" in response
    response_frame = pd.DataFrame(response["data"])
    # should have combination [adm, cl] [adm, u3], [cl, u3]
    assert response_frame["First Coder"].tolist() == [
        SEED_USERNAME,
        SEED_USERNAME,
        SEED_USERNAME2,
    ]
    assert response_frame["Second Coder"].tolist() == [
        SEED_USERNAME2,
        str(third_profile),
        str(third_profile),
    ]

    # check that the table has just those three combinations
    assert len(response_frame) == 3

    # should have "no samples" for combos with user3
    assert response_frame.loc[response_frame["Second Coder"] == str(third_profile)][
        "Percent Agreement"
    ].tolist() == ["No samples", "No samples"]

    # check that the percent agreement matches n%, n between 0 and 100
    perc = response_frame["Percent Agreement"].tolist()[0]
    assert float(perc[: len(perc) - 1]) <= 100 and float(perc[: len(perc) - 1]) >= 0


def test_heat_map_data(
    seeded_database,
    client,
    admin_client,
    test_project_all_irr_data,
    test_all_irr_all_queues,
    test_labels_all_irr,
):
    """This tests the heat map api call.

    Note: the exact values of the data are tested in util.
    """

    # sign in the users
    labels = test_labels_all_irr
    normal_queue, admin_queue, irr_queue = test_all_irr_all_queues
    project = test_project_all_irr_data

    client.login(username=SEED_USERNAME, password=SEED_PASSWORD)
    client_profile = Profile.objects.get(user__username=SEED_USERNAME)
    ProjectPermissions.objects.create(
        profile=client_profile, project=project, permission="CODER"
    )
    admin_client.login(username=SEED_USERNAME2, password=SEED_PASSWORD2)
    admin_profile = Profile.objects.get(user__username=SEED_USERNAME2)
    ProjectPermissions.objects.create(
        profile=admin_profile, project=project, permission="ADMIN"
    )
    third_profile = Profile.objects.get(user__username="test_profile")
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # non-admin should not be able to call the test
    response = client.get("/api/heat_map_data/" + str(project.pk) + "/")
    assert (
        403 == response.status_code
        and "Invalid permission. Must be an admin" in str(response.content)
    )

    # get the heatmap. Check that the list of coders and list of labels match
    response = admin_client.get("/api/heat_map_data/" + str(project.pk) + "/").json()
    project_labels = [label.name for label in labels]
    project_labels.append("Skip")
    assert_collections_equal(response["labels"], project_labels)

    coder_dict_list = []
    for prof in [admin_profile, client_profile, third_profile]:
        coder_dict_list.append({"name": prof.user.username, "pk": prof.pk})
    assert_collections_equal(response["coders"], coder_dict_list)

    # check that the heatmap has all combinations of users
    project_coders = [admin_profile.pk, client_profile.pk, third_profile.pk]
    for user1 in project_coders:
        for user2 in project_coders:
            user_combo = str(user1) + "_" + str(user2)
            assert user_combo in response["data"]
            # check that for each combo of users there is each combo of labels
            assert len(response["data"][user_combo]) == len(project_labels) ** 2
            label_frame = pd.DataFrame(response["data"][user_combo])
            label_frame["comb"] = label_frame["label1"] + "_" + label_frame["label2"]
            comb_list = []
            for lab1 in project_labels:
                for lab2 in project_labels:
                    comb_list.append(lab1 + "_" + lab2)
            assert_collections_equal(label_frame["comb"].tolist(), comb_list)


def test_label_distribution(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_labels,
    test_irr_queue,
    test_admin_queue,
):
    """This tests the api that produces the label counts chart for the admin page."""
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )

    response = client.get("/api/label_distribution/" + str(project.pk) + "/")
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )
    # at the beginning, should return empty list
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
        "/api/label_distribution/" + str(project.pk) + "/"
    ).json()
    assert len(response) > 0

    for row in response:
        temp_dict = row["values"]
        for label_dict in temp_dict:
            assert label_dict["x"] in [
                str(admin_profile),
                str(client_profile),
                "test_profile",
            ]
            if (
                label_dict["x"] == str(admin_profile)
                or label_dict["x"] == "test_profile"
            ):
                assert label_dict["y"] == 0
            else:
                assert label_dict["y"] == 1

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
        "/api/label_distribution/" + str(project.pk) + "/"
    ).json()
    assert len(response) > 0

    for row in response:
        label = row["key"]
        temp_dict = row["values"]
        for label_dict in temp_dict:
            assert label_dict["x"] in [
                str(admin_profile),
                str(client_profile),
                "test_profile",
            ]
            if label_dict["x"] == str(admin_profile):
                if label == test_labels[0].name:
                    assert label_dict["y"] == 3
                else:
                    assert label_dict["y"] == 0
            elif label_dict["x"] == "test_profile":
                assert label_dict["y"] == 0
            else:
                assert label_dict["y"] == 1


def test_label_timing(
    seeded_database,
    admin_client,
    client,
    test_project_data,
    test_queue,
    test_admin_queue,
    test_irr_queue,
    test_labels,
):
    # test that it starts out empty
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )

    response = client.get("/api/label_timing/" + str(project.pk) + "/")
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )

    response = admin_client.get("/api/label_timing/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 0
    assert response["yDomain"] == 0
    # have the client label three data with time=1
    data = get_assignments(client_profile, project, 3)
    response = client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 1},
    )
    response = client.post(
        "/api/annotate_data/" + str(data[1].pk) + "/",
        {"labelID": test_labels[1].pk, "labeling_time": 1},
    )
    response = client.post(
        "/api/annotate_data/" + str(data[2].pk) + "/",
        {"labelID": test_labels[2].pk, "labeling_time": 1},
    )

    # check that the quartiles are all the same
    response = admin_client.get("/api/label_timing/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 1

    quarts = response["data"][0]["values"]
    assert quarts["Q1"] == 1 and quarts["Q2"] == 1 and quarts["Q3"] == 1
    assert quarts["whisker_low"] == 1 and quarts["whisker_high"] == 1
    assert response["yDomain"] == 11

    # have the client label three data with 0, 3, 10. Check quartiles
    data = get_assignments(client_profile, project, 3)
    response = client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 0},
    )
    response = client.post(
        "/api/annotate_data/" + str(data[1].pk) + "/",
        {"labelID": test_labels[1].pk, "labeling_time": 3},
    )
    response = client.post(
        "/api/annotate_data/" + str(data[2].pk) + "/",
        {"labelID": test_labels[2].pk, "labeling_time": 10},
    )

    response = admin_client.get("/api/label_timing/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 1

    quarts = response["data"][0]["values"]
    assert quarts["Q1"] == 1 and quarts["Q2"] == 1 and quarts["Q3"] == 3
    assert quarts["whisker_low"] == 0 and quarts["whisker_high"] == 10
    assert response["yDomain"] == 20

    # have a client label with t=100. Check quartiles.
    data = get_assignments(client_profile, project, 1)
    response = client.post(
        "/api/annotate_data/" + str(data[0].pk) + "/",
        {"labelID": test_labels[0].pk, "labeling_time": 100},
    )
    response = admin_client.get("/api/label_timing/" + str(project.pk) + "/").json()
    quarts = response["data"][0]["values"]
    assert quarts["Q1"] == 1 and quarts["Q2"] == 1 and quarts["Q3"] == 10
    assert quarts["whisker_low"] == 0 and quarts["whisker_high"] == 100
    assert response["yDomain"] == 110


def test_model_metrics(
    seeded_database,
    admin_client,
    client,
    test_project_unlabeled_and_tfidf,
    test_queue,
    test_admin_queue,
    test_irr_queue,
    test_labels,
):
    """This function tests the model metrics api."""
    project = test_project_unlabeled_and_tfidf
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )
    # at the beginning, shouldn't have any
    for metric in ["accuracy", "f1", "precision", "recall"]:
        response = admin_client.get(
            "/api/model_metrics/" + str(project.pk) + "/?metric=" + metric
        ).json()
        if len(response) == 1:
            assert response[0]["key"] == "Accuracy"
        else:
            assert len(response) == len(test_labels)
        for temp_dict in response:
            assert len(temp_dict["values"]) == 0
    # label 30 items. The model should run.
    data = get_assignments(client_profile, project, 30)
    for i in range(30):
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": test_labels[i % 3].pk, "labeling_time": 1},
        )
    assert DataLabel.objects.filter(data__in=data).count() == 30

    # check that metrics were generated
    # for metric in ['accuracy', 'f1', 'precision', 'recall']:
    for metric in ["accuracy", "f1", "precision", "recall"]:
        response = admin_client.get(
            "/api/model_metrics/" + str(project.pk) + "/?metric=" + metric
        ).json()
        if len(response) == 1:
            assert response[0]["key"] == "Accuracy"
        else:
            assert len(response) == len(test_labels)

        # check there is some value for the first run
        for temp_dict in response:
            assert len(temp_dict["values"]) == 1
    # do this again and check that a new metric is generated
    fill_queue(test_queue, project.learning_method)

    data = get_assignments(client_profile, project, 30)
    for i in range(30):
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": test_labels[i % 3].pk, "labeling_time": 1},
        )

    fill_queue(test_queue, project.learning_method)

    data = get_assignments(client_profile, project, 10)
    for i in range(10):
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": test_labels[i % 3].pk, "labeling_time": 1},
        )

    for metric in ["accuracy", "f1", "precision", "recall"]:
        response = admin_client.get(
            "/api/model_metrics/" + str(project.pk) + "/?metric=" + metric
        ).json()
        if len(response) == 1:
            assert response[0]["key"] == "Accuracy"
        else:
            assert len(response) == len(test_labels)

        # check there is some value for the first run
        for temp_dict in response:
            assert len(temp_dict["values"]) == 2


def test_coded_table(
    seeded_database,
    client,
    admin_client,
    test_project_data,
    test_queue,
    test_admin_queue,
    test_irr_queue,
    test_labels,
):
    """This tests the table that displays the labeled table."""
    project = test_project_data
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )

    # first, check that it is empty
    response = client.get("/api/data_coded_table/" + str(project.pk) + "/")
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )

    response = admin_client.get("/api/data_coded_table/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 0
    # label a few things, and check that they are in the table
    data = get_assignments(client_profile, project, 3)
    data_text = []
    label_names = []
    for i in range(3):
        data_text.append(escape(data[i].text))
        label_names.append(test_labels[i].name)
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": test_labels[i].pk, "labeling_time": 1},
        )
    response = admin_client.get("/api/data_coded_table/" + str(project.pk) + "/").json()
    assert len(response["data"]) == 3
    for row in response["data"]:
        assert row["Text"] in data_text
        assert row["Label"] in label_names
        assert row["Coder"] == str(client_profile)


def test_predicted_table(
    seeded_database,
    admin_client,
    client,
    test_project_unlabeled_and_tfidf,
    test_queue,
    test_labels,
    test_irr_queue,
    test_admin_queue,
):
    """This tests that the predicted table contains what it should."""
    project = test_project_unlabeled_and_tfidf
    client_profile, admin_profile = sign_in_and_fill_queue(
        project, test_queue, client, admin_client
    )
    # first, check that it is empty
    response = client.get("/api/data_predicted_table/" + str(project.pk) + "/")
    assert (
        "detail" in response.json()
        and "Invalid permission. Must be an admin" in response.json()["detail"]
    )

    response = admin_client.get(
        "/api/data_predicted_table/" + str(project.pk) + "/"
    ).json()
    assert len(response["data"]) == 0

    # label 15 things and check that it is still empty
    data = get_assignments(client_profile, project, 15)
    data_text = []
    label_names = []
    for i in range(15):
        data_text.append(escape(data[i].text))
        label_names.append(test_labels[i % 3].name)
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": test_labels[i % 3].pk, "labeling_time": 1},
        )
    response = admin_client.get(
        "/api/data_predicted_table/" + str(project.pk) + "/"
    ).json()
    assert len(response["data"]) == 0
    # label 15 more things and let the predictions be created
    # check that the unlabeled items are in the table
    data = get_assignments(client_profile, project, 15)
    for i in range(15):
        data_text.append(escape(data[i].text))
        label_names.append(test_labels[i % 3].name)
        response = client.post(
            "/api/annotate_data/" + str(data[i].pk) + "/",
            {"labelID": test_labels[i % 3].pk, "labeling_time": 1},
        )
    response = admin_client.get(
        "/api/data_predicted_table/" + str(project.pk) + "/"
    ).json()

    training_set = TrainingSet.objects.get(
        set_number=project.get_current_training_set().set_number - 1
    )
    model = Model.objects.get(training_set=training_set)
    # check that the table holds the predicted data
    assert len(response["data"]) == (
        DataPrediction.objects.filter(data__project=project, model=model).count()
    ) // len(test_labels)
    # check that the table has the number of unlabeled data
    assert len(response["data"]) == (
        Data.objects.filter(project=project).count()
        - DataLabel.objects.filter(data__project=project).count()
    )
    # check that the table does not have the labeled data
    data_list = list(
        DataPrediction.objects.filter(data__project=project).values_list("data__text")
    )
    for d in data_text:
        assert d not in data_list

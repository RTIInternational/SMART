import os
from test.util import assert_obj_exists, read_test_data_backend

import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    Data,
    DataLabel,
    Label,
    Profile,
    Project,
    ProjectPermissions,
    TrainingSet,
)
from core.utils.util import (
    add_data,
    create_profile,
    create_project,
    get_labeled_data,
    irr_heatmap_data,
    perc_agreement_table_data,
    save_codebook_file,
    save_data_file,
)
from core.utils.utils_annotate import assign_datum, label_data, skip_data
from core.utils.utils_queue import fill_queue


def test_create_profile(db):
    username = "test_user"
    password = "password"
    email = "test_user@rti.org"

    create_profile(username, password, email)

    auth_user_attrs = {"username": username, "password": password, "email": email}

    assert_obj_exists(get_user_model(), auth_user_attrs)

    auth_user = get_user_model().objects.filter(**auth_user_attrs).first()

    assert_obj_exists(Profile, {"user": auth_user})


def test_create_project(db, test_profile):
    name = "test_project"
    create_project(name, test_profile)

    assert_obj_exists(Project, {"name": name})


def test_get_current_training_set_no_training_set(test_profile):
    project = Project.objects.create(name="test", creator=test_profile)

    training_set = project.get_current_training_set()

    assert training_set is None


def test_get_current_training_set_one_training_set(test_project):
    training_set = test_project.get_current_training_set()
    assertTrainingSet = TrainingSet.objects.filter(project=test_project).order_by(
        "-set_number"
    )[0]

    assert_obj_exists(TrainingSet, {"project": test_project, "set_number": 0})
    assert training_set == assertTrainingSet


def test_get_current_training_set_multiple_training_set(test_project):
    # Test Project already has training set with set number 0, create set number 1, 2, 3
    TrainingSet.objects.create(project=test_project, set_number=1)
    TrainingSet.objects.create(project=test_project, set_number=2)
    set_num_three = TrainingSet.objects.create(project=test_project, set_number=3)

    assert test_project.get_current_training_set() == set_num_three


def test_add_data_no_labels(db, test_project):
    test_data = read_test_data_backend(file="./core/data/test_files/test_no_labels.csv")
    df = add_data(test_project, test_data)

    for i, row in df.iterrows():
        assert_obj_exists(
            Data,
            {
                "upload_id_hash": row["id_hash"],
                "hash": row["hash"],
                "project": test_project,
            },
        )


def test_add_data_with_labels(db, test_project_labels):
    test_data = read_test_data_backend(
        file="./core/data/test_files/test_some_labels.csv"
    )
    df = add_data(test_project_labels, test_data)

    for i, row in df.iterrows():
        assert_obj_exists(
            Data,
            {
                "upload_id_hash": row["id_hash"],
                "hash": row["hash"],
                "project": test_project_labels,
            },
        )
        if not pd.isnull(row["Label"]):
            assert_obj_exists(
                DataLabel,
                {
                    "data__hash": row["hash"],
                    "profile": test_project_labels.creator,
                    "label__name": row["Label"],
                },
            )


def test_save_data_file_no_labels_csv(test_project, tmpdir, settings):
    test_file = "./core/data/test_files/test_no_labels.csv"

    temp_data_file_path = tmpdir.mkdir("data").mkdir("data_files")
    settings.PROJECT_FILE_PATH = str(temp_data_file_path)

    data = pd.read_csv(test_file)
    data["ID"] = data.index.tolist()
    data = data[["ID", "Text", "Label"]]

    fname = save_data_file(data, test_project.pk)

    saved_data = pd.read_csv(fname)

    assert fname == os.path.join(
        str(temp_data_file_path), "project_" + str(test_project.pk) + "_data_0.csv"
    )
    assert os.path.isfile(fname)
    assert saved_data.equals(data)


def test_save_data_file_some_labels_csv(test_project, tmpdir, settings):
    test_file = "./core/data/test_files/test_some_labels.csv"

    temp_data_file_path = tmpdir.mkdir("data").mkdir("data_files")
    settings.PROJECT_FILE_PATH = str(temp_data_file_path)

    data = pd.read_csv(test_file)
    data["ID"] = data.index.tolist()
    data = data[["ID", "Text", "Label"]]

    fname = save_data_file(data, test_project.pk)

    saved_data = pd.read_csv(fname)

    assert fname == os.path.join(
        str(temp_data_file_path), "project_" + str(test_project.pk) + "_data_0.csv"
    )
    assert os.path.isfile(fname)
    assert saved_data.equals(data)


def test_save_data_file_multiple_files(test_project, tmpdir, settings):
    test_file = "./core/data/test_files/test_no_labels.csv"

    temp_data_file_path = tmpdir.mkdir("data").mkdir("data_files")
    settings.PROJECT_FILE_PATH = str(temp_data_file_path)

    data = pd.read_csv(test_file)
    data["ID"] = data.index.tolist()

    fname1 = save_data_file(data, test_project.pk)
    fname2 = save_data_file(data, test_project.pk)
    fname3 = save_data_file(data, test_project.pk)

    assert fname1 == os.path.join(
        str(temp_data_file_path), "project_" + str(test_project.pk) + "_data_0.csv"
    )
    assert os.path.isfile(fname1)
    assert fname2 == os.path.join(
        str(temp_data_file_path), "project_" + str(test_project.pk) + "_data_1.csv"
    )
    assert os.path.isfile(fname2)
    assert fname3 == os.path.join(
        str(temp_data_file_path), "project_" + str(test_project.pk) + "_data_2.csv"
    )
    assert os.path.isfile(fname3)


def test_save_codebook(test_project, tmpdir, settings):
    """This tests that a user can upload a pdf codebook and have it be saved properly
    internally."""
    test_file = open("./core/data/test_files/test_codebook.pdf", "rb")

    temp_data_file_path = tmpdir.mkdir("data").mkdir("code_books")
    settings.CODEBOOK_FILE_PATH = str(temp_data_file_path)

    fname = save_codebook_file(test_file, test_project.pk)
    date = timezone.now().strftime("%m_%d_%y__%H_%M_%S")
    f_path = os.path.join(
        str(temp_data_file_path),
        "project_" + str(test_project.pk) + "_codebook" + date + ".pdf",
    )
    assert fname == f_path.replace("/data/code_books/", "")
    assert os.path.isfile(f_path)


def test_heatmap_data(
    setup_celery,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_profile,
    test_profile2,
    test_labels_half_irr,
    test_redis,
    tmpdir,
    settings,
):
    """These tests check that the heatmap accurately reflects the data."""
    project = test_project_half_irr_data
    ProjectPermissions.objects.create(
        profile=test_profile, project=project, permission="CODER"
    )
    ProjectPermissions.objects.create(
        profile=test_profile2, project=project, permission="CODER"
    )
    labels = test_labels_half_irr
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    combo1 = str(test_profile.pk) + "_" + str(test_profile2.pk)

    same1 = str(test_profile.pk) + "_" + str(test_profile.pk)
    same2 = str(test_profile2.pk) + "_" + str(test_profile2.pk)

    # don't label anything. The heatmap shoud have all zeros for user pair
    heatmap = irr_heatmap_data(project)
    assert combo1 in heatmap
    heatmap = heatmap[combo1]

    counts = pd.DataFrame(heatmap)["count"].tolist()
    assert np.all(np.equal(counts, [0] * len(counts)))

    # have one user skip 3 things and another label them.
    for i in range(3):
        datum = assign_datum(test_profile, project, "irr")
        assign_datum(test_profile2, project, "irr")
        label_data(labels[i], datum, test_profile, 3)
        skip_data(datum, test_profile2)

    # check that user1-user1 map is I3
    heatmap = irr_heatmap_data(project)
    same_frame = pd.DataFrame(heatmap[same1])
    assert (
        same_frame.loc[
            (same_frame["label1"] == labels[0].name)
            & (same_frame["label2"] == labels[0].name)
        ]["count"].tolist()[0]
        == 1
    )
    assert (
        same_frame.loc[
            (same_frame["label1"] == labels[1].name)
            & (same_frame["label2"] == labels[1].name)
        ]["count"].tolist()[0]
        == 1
    )
    assert (
        same_frame.loc[
            (same_frame["label1"] == labels[2].name)
            & (same_frame["label2"] == labels[2].name)
        ]["count"].tolist()[0]
        == 1
    )
    assert np.sum(same_frame["count"].tolist()) == 3

    # check the second user only has 3 in the skip-skip spot
    same_frame2 = pd.DataFrame(heatmap[same2])
    assert (
        same_frame2.loc[
            (same_frame2["label1"] == "Skip") & (same_frame["label2"] == "Skip")
        ]["count"].tolist()[0]
        == 3
    )
    assert np.sum(same_frame2["count"].tolist()) == 3

    # check that the between-user heatmap has skip-label = 1 for each label
    heatmap = irr_heatmap_data(project)
    heatmap = pd.DataFrame(heatmap[combo1])
    assert (
        heatmap.loc[
            (heatmap["label1"] == labels[0].name) & (heatmap["label2"] == "Skip")
        ]["count"].tolist()[0]
        == 1
    )
    assert (
        heatmap.loc[
            (heatmap["label1"] == labels[1].name) & (heatmap["label2"] == "Skip")
        ]["count"].tolist()[0]
        == 1
    )
    assert (
        heatmap.loc[
            (heatmap["label1"] == labels[2].name) & (heatmap["label2"] == "Skip")
        ]["count"].tolist()[0]
        == 1
    )

    assert np.sum(heatmap["count"].tolist()) == 3

    # have users agree on 5 labels and datums, check heatmap
    for i in range(5):
        datum = assign_datum(test_profile, project, "irr")
        assign_datum(test_profile2, project, "irr")
        label_data(labels[i % 3], datum, test_profile, 3)
        label_data(labels[i % 3], datum, test_profile2, 3)

    heatmap = irr_heatmap_data(project)
    heatmap = pd.DataFrame(heatmap[combo1])

    assert (
        heatmap.loc[
            (heatmap["label1"] == labels[0].name)
            & (heatmap["label2"] == labels[0].name)
        ]["count"].tolist()[0]
        == 2
    )
    assert (
        heatmap.loc[
            (heatmap["label1"] == labels[1].name)
            & (heatmap["label2"] == labels[1].name)
        ]["count"].tolist()[0]
        == 2
    )
    assert (
        heatmap.loc[
            (heatmap["label1"] == labels[2].name)
            & (heatmap["label2"] == labels[2].name)
        ]["count"].tolist()[0]
        == 1
    )
    assert np.sum(heatmap["count"].tolist()) == 8

    # have one user label something, show the heatmap hasn't changed
    datum = assign_datum(test_profile, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    heatmap = irr_heatmap_data(project)
    same_map = heatmap[same1]
    assert np.sum(pd.DataFrame(same_map)["count"].tolist()) == 8
    heatmap = pd.DataFrame(heatmap[combo1])
    assert np.sum(pd.DataFrame(heatmap)["count"].tolist()) == 8


def test_percent_agreement_table(
    setup_celery,
    test_project_all_irr_3_coders_data,
    test_all_irr_3_coders_all_queues,
    test_profile,
    test_profile2,
    test_profile3,
    test_labels_all_irr_3_coders,
    test_redis,
    tmpdir,
    settings,
):
    """This tests the percent agreement table."""
    project = test_project_all_irr_3_coders_data
    ProjectPermissions.objects.create(
        profile=test_profile2, project=project, permission="CODER"
    )
    ProjectPermissions.objects.create(
        profile=test_profile3, project=project, permission="CODER"
    )
    labels = test_labels_all_irr_3_coders
    normal_queue, admin_queue, irr_queue = test_all_irr_3_coders_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    table_data_perc = pd.DataFrame(perc_agreement_table_data(project))[
        "Percent Agreement"
    ].tolist()
    # first test that it has "No Samples" for the percent for all
    assert len(table_data_perc) == 3
    assert (
        (table_data_perc[0] == "No samples")
        and (table_data_perc[1] == "No samples")
        and (table_data_perc[2] == "No samples")
    )

    # First have everyone give same label, should be 100% for all
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[0], datum, test_profile2, 3)
    label_data(labels[0], datum, test_profile3, 3)

    table_data_perc = pd.DataFrame(perc_agreement_table_data(project))[
        "Percent Agreement"
    ].tolist()
    assert (
        (table_data_perc[0] == "100.0%")
        and (table_data_perc[1] == "100.0%")
        and (table_data_perc[2] == "100.0%")
    )

    # Next have user1 = user2 != user3, Check values
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[0], datum, test_profile2, 3)
    label_data(labels[1], datum, test_profile3, 3)

    table_data_perc = pd.DataFrame(perc_agreement_table_data(project))[
        "Percent Agreement"
    ].tolist()
    # goes in the order [prof2,prof3], [prof2, prof], [prof3, prof]
    assert (
        (table_data_perc[0] == "50.0%")
        and (table_data_perc[1] == "100.0%")
        and (table_data_perc[2] == "50.0%")
    )

    # Next have all users skip. Should count as disagreement.
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    skip_data(datum, test_profile)
    skip_data(datum, test_profile2)
    skip_data(datum, test_profile3)

    table_data_perc = pd.DataFrame(perc_agreement_table_data(project))[
        "Percent Agreement"
    ].tolist()
    # goes in the order [prof2,prof3], [prof2, prof], [prof3, prof]
    assert (
        (table_data_perc[0] == "33.3%")
        and (table_data_perc[1] == "66.7%")
        and (table_data_perc[2] == "33.3%")
    )

    # Lastly have two users label. Should be the same as before
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[0], datum, test_profile2, 3)
    table_data_perc = pd.DataFrame(perc_agreement_table_data(project))[
        "Percent Agreement"
    ].tolist()
    # goes in the order [prof2,prof3], [prof2, prof], [prof3, prof]
    assert (
        (table_data_perc[0] == "33.3%")
        and (table_data_perc[1] == "66.7%")
        and (table_data_perc[2] == "33.3%")
    )


def test_get_labeled_data(
    setup_celery,
    test_profile,
    test_project_labeled,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_admin_queue_labeled,
    test_redis,
    tmpdir,
    settings,
):
    """This tests that the labeled data is pulled correctly."""
    # This tests labeled data util call
    project = test_project_labeled
    project_labels = Label.objects.filter(project=project)
    fill_queue(
        test_queue_labeled,
        "random",
        test_irr_queue_labeled,
        project.percentage_irr,
        project.batch_size,
    )

    # get the labeled data and the labels
    labeled_data, labels = get_labeled_data(project)
    assert isinstance(labeled_data, pd.DataFrame)
    assert isinstance(labels, pd.DataFrame)

    # should have the same number of labels and labeled data as in project
    assert len(labels) == len(project_labels)

    project_labeled = DataLabel.objects.filter(data__project=project)
    assert len(labeled_data) == len(project_labeled)

    # check that the labeled data is returned matches the stuff in DataLabel
    assert len(
        set(project_labeled.values_list("data__upload_id", flat=True))
        & set(labeled_data["ID"].tolist())
    ) == len(labeled_data)

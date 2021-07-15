import os
from test.conftest import TEST_QUEUE_LEN
from test.util import assert_obj_exists, assert_redis_matches_db

import numpy as np
import pytest

from core.models import (
    Data,
    DataLabel,
    DataPrediction,
    DataQueue,
    DataUncertainty,
    Model,
    ProjectPermissions,
)
from core.utils.utils_annotate import assign_datum, label_data
from core.utils.utils_model import (
    check_and_trigger_model,
    cohens_kappa,
    entropy,
    fleiss_kappa,
    least_confident,
    load_tfidf_matrix,
    margin_sampling,
    predict_data,
    save_tfidf_matrix,
    train_and_save_model,
)
from core.utils.utils_queue import fill_queue, find_queue_length
from core.utils.utils_redis import get_ordered_data


def test_create_tfidf_matrix(test_tfidf_matrix):
    # UPDATE: is now saved as a dictionary of lists
    assert isinstance(test_tfidf_matrix, dict)
    assert len(test_tfidf_matrix) == 982
    for key in test_tfidf_matrix:
        assert len(test_tfidf_matrix[key]) == 162
        assert np.all([type(val) == float for val in test_tfidf_matrix[key]])


def test_save_tfidf_matrix(test_project_data, test_tfidf_matrix, tmpdir, settings):
    data_temp = tmpdir.mkdir("data").mkdir("tf_idf")
    settings.TF_IDF_PATH = str(data_temp)

    file = save_tfidf_matrix(test_tfidf_matrix, test_project_data.pk)

    assert os.path.isfile(file)
    assert file == os.path.join(
        settings.TF_IDF_PATH,
        "project_" + str(test_project_data.pk) + "_tfidf_matrix.pkl",
    )


def test_load_tfidf_matrix(
    test_project_labeled_and_tfidf, test_tfidf_matrix_labeled, tmpdir, settings
):
    matrix = load_tfidf_matrix(test_project_labeled_and_tfidf.pk)

    for key in matrix:
        assert key in test_tfidf_matrix_labeled
        assert np.allclose(matrix[key], test_tfidf_matrix_labeled[key])


def test_least_confident_notarray():
    probs = [0.5, 0.5]

    with pytest.raises(ValueError) as excinfo:
        least_confident(probs)

    assert "Probs should be a numpy array" in str(excinfo.value)


def test_least_confident_threeclass():
    probs = np.array([0.1, 0.3, 0.6])

    lc = least_confident(probs)

    np.testing.assert_almost_equal(lc, 0.4)


def test_least_confident_binary():
    probs = np.array([0.2, 0.8])

    lc = least_confident(probs)

    np.testing.assert_almost_equal(lc, 0.2)


def test_least_confident_fourclass():
    probs = np.array([0.1, 0.1, 0.1, 0.7])

    lc = least_confident(probs)

    np.testing.assert_almost_equal(lc, 0.3)


def test_margin_sampling_notarray():
    probs = [0.5, 0.5]

    with pytest.raises(ValueError) as excinfo:
        margin_sampling(probs)

    assert "Probs should be a numpy array" in str(excinfo.value)


def test_margin_sampling_threeclass():
    probs = np.array([0.1, 0.3, 0.6])

    ms = margin_sampling(probs)

    np.testing.assert_almost_equal(ms, 0.3)


def test_margin_sampling_binary():
    probs = np.array([0.2, 0.8])

    ms = margin_sampling(probs)

    np.testing.assert_almost_equal(ms, 0.6)


def test_margin_sampling_fourclass():
    probs = np.array([0.1, 0.1, 0.1, 0.7])

    ms = margin_sampling(probs)

    np.testing.assert_almost_equal(ms, 0.6)


def test_margin_sampling_array_ordering():
    probs = np.array([0.9, 0.3, 0.1, 0.4, 0.5])
    probs[::-1].sort()

    assert probs[0] > probs[1]


def test_entropy_notarray():
    probs = [0.5, 0.5]

    with pytest.raises(ValueError) as excinfo:
        entropy(probs)

    assert "Probs should be a numpy array" in str(excinfo.value)


def test_entropy_threeclass():
    probs = np.array([0.1, 0.3, 0.6])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.3899728733539152)


def test_entropy_binary():
    probs = np.array([0.2, 0.8])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.21732201127364886)


def test_entropy_fourclass():
    probs = np.array([0.1, 0.1, 0.1, 0.7])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.4084313719900203)


def test_entropy_with_zero():
    probs = np.array([0, 0.3, 0.7])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.26529499557412151)


def test_train_and_save_model(test_project_labeled_and_tfidf, tmpdir, settings):
    project = test_project_labeled_and_tfidf

    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    model = train_and_save_model(project)

    assert isinstance(model, Model)
    assert_obj_exists(Model, {"pickle_path": model.pickle_path, "project": project})
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(project.get_current_training_set().set_number)
        + ".pkl",
    )


def test_predict_data(test_project_with_trained_model, tmpdir):
    project = test_project_with_trained_model

    predictions = predict_data(project, project.model_set.get())

    # Number of unlabeled data * number of labels.  Each data gets a prediction for each label.
    expected_predction_count = (
        project.data_set.filter(datalabel__isnull=True).count() * project.labels.count()
    )
    assert len(predictions) == expected_predction_count

    for prediction in predictions:
        assert isinstance(prediction, DataPrediction)
        assert_obj_exists(
            DataPrediction,
            {
                "data": prediction.data,
                "model": prediction.model,
                "label": prediction.label,
                "predicted_probability": prediction.predicted_probability,
            },
        )


def test_check_and_trigger_model_first_labeled(
    setup_celery, test_project_data, test_labels, test_queue, test_profile
):
    initial_training_set = test_project_data.get_current_training_set()

    fill_queue(test_queue, orderby="random")

    datum = assign_datum(test_profile, test_queue.project)
    test_label = test_labels[0]
    label_data(test_label, datum, test_profile, 3)

    check = check_and_trigger_model(datum)
    assert check == "no trigger"

    assert test_project_data.get_current_training_set() == initial_training_set
    assert test_project_data.model_set.count() == 0
    assert DataPrediction.objects.filter(data__project=test_project_data).count() == 0
    assert DataUncertainty.objects.filter(data__project=test_project_data).count() == 0
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN - 1


def test_check_and_trigger_lt_batch_labeled(
    setup_celery, test_project_data, test_labels, test_queue, test_profile
):
    initial_training_set = test_project_data.get_current_training_set()

    fill_queue(test_queue, orderby="random")

    for i in range(TEST_QUEUE_LEN // 2):
        datum = assign_datum(test_profile, test_queue.project)
        test_label = test_labels[0]
        label_data(test_label, datum, test_profile, 3)

    check = check_and_trigger_model(datum)
    assert check == "no trigger"

    assert test_project_data.get_current_training_set() == initial_training_set
    assert test_project_data.model_set.count() == 0
    assert DataPrediction.objects.filter(data__project=test_project_data).count() == 0
    assert DataUncertainty.objects.filter(data__project=test_project_data).count() == 0
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN - (
        TEST_QUEUE_LEN // 2
    )


def test_check_and_trigger_batched_success(
    setup_celery,
    test_project_labeled_and_tfidf,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_redis,
    tmpdir,
    settings,
):
    project = test_project_labeled_and_tfidf
    test_queue = test_queue_labeled
    initial_training_set = project.get_current_training_set()
    initial_queue_size = test_queue.length
    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    datum = DataLabel.objects.filter(data__project=project).first().data
    check = check_and_trigger_model(datum)
    assert check == "model running"

    # Assert model created and saved
    assert_obj_exists(Model, {"project": project})
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(initial_training_set.set_number)
        + ".pkl",
    )

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert (
        len(predictions)
        == Data.objects.filter(project=project, labelers=None).count()
        * project.labels.count()
    )

    # Assert queue filled and redis sycned
    assert (
        test_queue.data.count() + test_irr_queue_labeled.data.count()
    ) == test_queue.length
    assert_redis_matches_db(test_redis)
    assert test_queue.length == initial_queue_size

    # Assert least confident in queue
    data_list = get_ordered_data(test_queue.data.all(), "least confident")
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident
    assert (
        DataQueue.objects.filter(queue=test_queue).count()
        + DataQueue.objects.filter(queue=test_irr_queue_labeled).count()
    ) == TEST_QUEUE_LEN

    # Assert new training set
    assert project.get_current_training_set() != initial_training_set
    assert (
        project.get_current_training_set().set_number
        == initial_training_set.set_number + 1
    )


def test_check_and_trigger_batched_onlyone_label(
    setup_celery, test_project_data, test_labels, test_queue, test_profile
):
    initial_training_set = test_project_data.get_current_training_set()

    fill_queue(test_queue, orderby="random")

    for i in range(TEST_QUEUE_LEN):
        datum = assign_datum(test_profile, test_queue.project)
        test_label = test_labels[0]
        label_data(test_label, datum, test_profile, 3)

    check = check_and_trigger_model(datum)
    assert check == "random"

    assert test_project_data.get_current_training_set() == initial_training_set
    assert test_project_data.model_set.count() == 0
    assert DataPrediction.objects.filter(data__project=test_project_data).count() == 0
    assert DataUncertainty.objects.filter(data__project=test_project_data).count() == 0
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN


def test_check_and_trigger_queue_changes_success(
    setup_celery,
    test_project_labeled_and_tfidf,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_redis,
    tmpdir,
    settings,
    test_profile2,
):
    project = test_project_labeled_and_tfidf
    test_queue = test_queue_labeled
    initial_training_set = project.get_current_training_set()
    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    # Add another user to permissions
    ProjectPermissions.objects.create(
        profile=test_profile2, project=project, permission="CODER"
    )

    datum = DataLabel.objects.filter(data__project=project).first().data
    check = check_and_trigger_model(datum)
    assert check == "model running"

    # Assert model created and saved
    assert_obj_exists(Model, {"project": project})
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(initial_training_set.set_number)
        + ".pkl",
    )

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert (
        len(predictions)
        == Data.objects.filter(project=project, labelers=None).count()
        * project.labels.count()
    )

    # Assert queue filled and redis sycned
    batch_size = project.batch_size
    q = project.queue_set.get(type="normal")
    q_irr = project.queue_set.get(type="irr")
    assert (q.data.count() + q_irr.data.count()) == batch_size
    assert_redis_matches_db(test_redis)

    num_coders = len(project.projectpermissions_set.all()) + 1
    new_queue_length = find_queue_length(batch_size, num_coders)
    assert q.length == new_queue_length

    # Assert least confident in queue
    data_list = get_ordered_data(test_queue.data.all(), "least confident")
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident
    assert (
        DataQueue.objects.filter(queue=test_queue).count()
        + DataQueue.objects.filter(queue=test_irr_queue_labeled).count()
    ) == batch_size

    # Assert new training set
    assert project.get_current_training_set() != initial_training_set
    assert (
        project.get_current_training_set().set_number
        == initial_training_set.set_number + 1
    )


def test_svm_classifier(
    setup_celery,
    test_project_svm_data_tfidf,
    test_svm_labels,
    test_svm_queue_list,
    test_profile,
    test_redis,
    tmpdir,
    settings,
):
    """This tests that a project with the svm classifier can successfully train and give
    predictions for a model."""
    normal_queue, admin_queue, irr_queue = test_svm_queue_list
    labels = test_svm_labels
    project = test_project_svm_data_tfidf

    active_l = project.learning_method
    batch_size = project.batch_size
    initial_training_set = project.get_current_training_set()
    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    assert project.classifier == "svm"
    assert active_l == "least confident"

    fill_queue(normal_queue, "random")

    assert DataQueue.objects.filter(queue=normal_queue).count() == batch_size

    for i in range(batch_size):
        datum = assign_datum(test_profile, project)
        label_data(labels[i % 3], datum, test_profile, 3)

    ret_str = check_and_trigger_model(datum)
    assert ret_str == "model running"

    # Assert model created and saved
    assert_obj_exists(Model, {"project": project})
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(initial_training_set.set_number)
        + ".pkl",
    )

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert (
        len(predictions)
        == Data.objects.filter(project=project, labelers=None).count()
        * project.labels.count()
    )


def test_randomforest_classifier(
    setup_celery,
    test_project_randomforest_data_tfidf,
    test_randomforest_labels,
    test_randomforest_queue_list,
    test_profile,
    test_redis,
    tmpdir,
    settings,
):
    """This tests that a project with the random forest classifier can successfully
    train and give predictions for a model."""
    normal_queue, admin_queue, irr_queue = test_randomforest_queue_list
    labels = test_randomforest_labels
    project = test_project_randomforest_data_tfidf

    active_l = project.learning_method
    batch_size = project.batch_size
    initial_training_set = project.get_current_training_set()
    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    assert project.classifier == "random forest"
    assert active_l == "least confident"

    fill_queue(normal_queue, "random")

    assert DataQueue.objects.filter(queue=normal_queue).count() == batch_size

    for i in range(batch_size):
        datum = assign_datum(test_profile, project)
        label_data(labels[i % 3], datum, test_profile, 3)

    ret_str = check_and_trigger_model(datum)
    assert ret_str == "model running"

    # Assert model created and saved
    assert_obj_exists(Model, {"project": project})
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(initial_training_set.set_number)
        + ".pkl",
    )

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert (
        len(predictions)
        == Data.objects.filter(project=project, labelers=None).count()
        * project.labels.count()
    )


def test_g_naivebayes_classifier(
    setup_celery,
    test_project_gnb_data_tfidf,
    test_gnb_labels,
    test_gnb_queue_list,
    test_profile,
    test_redis,
    tmpdir,
    settings,
):
    """This tests that a project with the Gaussian Naiive Bayes classifier can
    successfully train and give predictions for a model."""
    normal_queue, admin_queue, irr_queue = test_gnb_queue_list
    labels = test_gnb_labels
    project = test_project_gnb_data_tfidf

    active_l = project.learning_method
    batch_size = project.batch_size
    initial_training_set = project.get_current_training_set()
    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    assert project.classifier == "gnb"
    assert active_l == "least confident"

    fill_queue(normal_queue, "random")

    assert DataQueue.objects.filter(queue=normal_queue).count() == batch_size

    for i in range(batch_size):
        datum = assign_datum(test_profile, project)
        label_data(labels[i % 3], datum, test_profile, 3)

    ret_str = check_and_trigger_model(datum)
    assert ret_str == "model running"

    # Assert model created and saved
    assert_obj_exists(Model, {"project": project})
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(initial_training_set.set_number)
        + ".pkl",
    )

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert (
        len(predictions)
        == Data.objects.filter(project=project, labelers=None).count()
        * project.labels.count()
    )


def test_cohens_kappa_perc_agreement(
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
    """want to check several different configurations including empty, no agreement
    Should throw an error if no irr data processed yet."""
    project = test_project_half_irr_data
    labels = test_labels_half_irr
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # check that before anything is labeled, an error is thrown
    with pytest.raises(ValueError) as excinfo:
        cohens_kappa(project)
    assert "No irr data" in str(excinfo.value)

    # have two labelers label two datum the same.
    for i in range(2):
        datum = assign_datum(test_profile, project, "irr")
        assign_datum(test_profile2, project, "irr")
        label_data(labels[0], datum, test_profile, 3)
        label_data(labels[0], datum, test_profile2, 3)

    # kappa requires at least two labels be represented
    with pytest.raises(ValueError) as excinfo:
        cohens_kappa(project)
    assert "Need at least two labels represented" in str(excinfo.value)

    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    label_data(labels[1], datum, test_profile, 3)
    label_data(labels[1], datum, test_profile2, 3)

    # Now kappa should be 1
    kappa, perc = cohens_kappa(project)
    assert kappa == 1.0
    assert perc == 1.0

    # have two labelers disagree on two datum check the value
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    label_data(labels[1], datum, test_profile, 3)
    label_data(labels[2], datum, test_profile2, 3)

    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[1], datum, test_profile2, 3)

    kappa, perc = cohens_kappa(project)
    assert round(kappa, 3) == 0.333
    assert perc == 0.6


def test_cohens_kappa_perc_agreement_no_agreement(
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
    """This just tests the kappa and percent if nobody ever agreed."""
    project = test_project_half_irr_data
    labels = test_labels_half_irr
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # label 5 irr elements but disagree on all of them
    for i in range(5):
        datum = assign_datum(test_profile, project, "irr")
        assign_datum(test_profile2, project, "irr")
        label_data(labels[i % 3], datum, test_profile, 3)
        label_data(labels[(i + 1) % 3], datum, test_profile2, 3)
    kappa, perc = cohens_kappa(project)
    assert round(kappa, 3) == -0.471
    assert perc == 0.0


def test_fleiss_kappa_perc_agreement(
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
    """This tests the results of the Fleiss's kappa function when fed different
    situations."""
    project = test_project_all_irr_3_coders_data
    labels = test_labels_all_irr_3_coders
    normal_queue, admin_queue, irr_queue = test_all_irr_3_coders_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # first check that an error is thrown if there is no data
    with pytest.raises(ValueError) as excinfo:
        fleiss_kappa(project)
    assert "No irr data" in str(excinfo.value)

    # next, check that the same error happens if only two have labeled it
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[1], datum, test_profile2, 3)

    with pytest.raises(ValueError) as excinfo:
        fleiss_kappa(project)
    assert "No irr data" in str(excinfo.value)

    # have everyone label a datum differenty
    # [1 1 1], kappa = -0.5, pa = 0
    label_data(labels[2], datum, test_profile3, 3)
    kappa, perc = fleiss_kappa(project)
    assert round(kappa, 1) == -0.5
    assert perc == 0.0

    # have only two people label a datum the same and check that kappa is the same
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[0], datum, test_profile2, 3)

    kappa, perc = fleiss_kappa(project)
    assert round(kappa, 1) == -0.5
    assert perc == 0.0

    # have last person label datum the same
    # [[1 1 1],[3 0 0]], kappa = 0.0, pa = 0.5
    label_data(labels[0], datum, test_profile3, 3)

    kappa, perc = fleiss_kappa(project)
    assert round(kappa, 2) == 0.0
    assert perc == 0.5

    # have two people agree and one disagree
    # [[1 1 1],[3 0 0],[2 1 0]], kappa = -0.13, pa=0.333
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[0], datum, test_profile2, 3)
    label_data(labels[1], datum, test_profile3, 3)

    kappa, perc = fleiss_kappa(project)
    assert round(kappa, 2) == -0.13
    assert round(perc, 2) == 0.33

    # repeat previous step with slight variation
    # [[1 1 1],[3 0 0],[2 1 0],[1 2 0]], kappa = -0.08, pa=0.25
    datum = assign_datum(test_profile, project, "irr")
    assign_datum(test_profile2, project, "irr")
    assign_datum(test_profile3, project, "irr")
    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[1], datum, test_profile2, 3)
    label_data(labels[1], datum, test_profile3, 3)

    kappa, perc = fleiss_kappa(project)
    assert round(kappa, 2) == -0.08
    assert round(perc, 2) == 0.25

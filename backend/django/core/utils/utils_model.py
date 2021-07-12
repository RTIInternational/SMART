import math
import os
import pickle

import joblib
import numpy as np
import pandas as pd
import statsmodels.stats.inter_rater as raters
from django.conf import settings
from scipy import sparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import cross_val_predict
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

from core import tasks
from core.models import (
    Data,
    DataLabel,
    DataPrediction,
    DataUncertainty,
    IRRLog,
    Label,
    Model,
    RecycleBin,
)
from core.utils.utils_queue import fill_queue, handle_empty_queue


def cohens_kappa(project):
    """
    Takes in the irr log data and calculates cohen's kappa
    NOTE: this should only be used if the num_users_irr = 2
    https://onlinecourses.science.psu.edu/stat509/node/162/
    https://en.wikipedia.org/wiki/Cohen%27s_kappa
    """
    irr_data = set(IRRLog.objects.values_list("data", flat=True))

    agree = 0

    # initialize the dictionary
    rater1_rater2_dict = {}
    label_list = list(
        Label.objects.filter(project=project).values_list("name", flat=True)
    )
    label_list.append("skip")
    for label1 in label_list:
        rater1_rater2_dict[label1] = {}
        for label2 in label_list:
            rater1_rater2_dict[label1][label2] = 0

    num_data = 0
    labels_seen = set()
    for d in irr_data:
        d_log = IRRLog.objects.filter(data=d, data__project=project)
        labels = list(set(d_log.values_list("label", flat=True)))
        labels_seen = labels_seen | set(labels)
        # get the percent agreement between the users  = (num agree)/size_data
        if d_log.count() < 2:
            # don't use this datum, it isn't processed yet
            continue
        num_data += 1
        if len(labels) == 1:
            if labels[0] is not None:
                agree += 1
        if d_log[0].label is None:
            label1 = "skip"
        else:
            label1 = d_log[0].label.name

        if d_log[1].label is None:
            label2 = "skip"
        else:
            label2 = d_log[1].label.name

        rater1_rater2_dict[label1][label2] += 1
    if num_data == 0:
        # there is no irr data, so just return bad values
        raise ValueError("No irr data")

    if len(labels_seen) < 2:
        raise ValueError("Need at least two labels represented")

    kappa = raters.cohens_kappa(
        np.asarray(pd.DataFrame(rater1_rater2_dict)), return_results=False
    )

    p_o = agree / num_data
    return kappa, p_o


def fleiss_kappa(project):
    """Takes in the irr log data and calculates fleiss's kappa Code modified from:

    https://gist.github.com/skylander86/65c442356377367e27e79ef1fed4adee
    Equations from: https://en.wikipedia.org/wiki/Fleiss%27_kappa
    """
    irr_data = set(IRRLog.objects.values_list("data", flat=True))

    label_list = list(
        Label.objects.filter(project=project).values_list("name", flat=True)
    )
    label_list.append(None)

    # n is the number of labelers
    n = project.num_users_irr
    agree = 0
    data_label_dict = []
    num_data = 0
    for d in irr_data:
        d_data_log = IRRLog.objects.filter(data=d, data__project=project)

        if d_data_log.count() < n:
            # don't use this datum, it isn't processed yet
            continue
        elif d_data_log.count() > n:
            # grab only the first few elements if there were extra labelers
            d_data_log = d_data_log[:n]
        num_data += 1
        labels = list(set(d_data_log.values_list("label", flat=True)))
        # accumulate the percent agreement
        if len(labels) == 1:
            if labels[0] is not None:
                agree += 1

        label_count_dict = {}
        for label in label_list:
            if label is None:
                l_label = "skip"
            else:
                l_label = str(label)
            label_count_dict[l_label] = len(d_data_log.filter(label__name=label))

        data_label_dict.append(label_count_dict)

    if num_data == 0:
        # there is no irr data, so just return bad values
        raise ValueError("No irr data")

    kappa = raters.fleiss_kappa(np.asarray(pd.DataFrame(data_label_dict)))

    return kappa, agree / num_data


def least_confident(probs):
    """Least Confident.

        x = 1 - p
        p is probability of highest probability class

    Args:
        probs: List of predicted probabilites
    Returns:
        x
    """
    if not isinstance(probs, np.ndarray):
        raise ValueError("Probs should be a numpy array")

    max_prob = max(probs)
    return 1 - max_prob


def margin_sampling(probs):
    """Margin Sampling.

        x = p1 - p2
        p1 is probabiiity of highest probability class
        p2 is probability of lowest probability class
    Args:
        probs: List of predicted probabilities
    Returns:
        x
    """
    if not isinstance(probs, np.ndarray):
        raise ValueError("Probs should be a numpy array")

    # https://stackoverflow.com/questions/26984414/efficiently-sorting-a-numpy-array-in-descending-order#answer-26984520
    probs[::-1].sort()
    return probs[0] - probs[1]


def entropy(probs):
    """Entropy - Uncertainty Sampling
        x = -sum(p * log(p))
        the sum is sumation across p's
    Args:
        probs: List of predicted probabilities
    Returns:
        x
    """
    if not isinstance(probs, np.ndarray):
        raise ValueError("Probs should be a numpy array")

    non_zero_probs = (p for p in probs if p > 0)

    total = 0
    for p in non_zero_probs:
        total += p * math.log10(p)

    return -total


def check_and_trigger_model(datum, profile=None):
    """Given a recently assigned datum check if the project it belong to needs its model
    ran.  It the model needs to be run, start the model run and create a new project
    current_training_set.

    Args:
        datum: Data object (may or may not be labeled)
    Returns:
        return_str: String to represent which path the function took
    """
    project = datum.project
    current_training_set = project.get_current_training_set()
    batch_size = project.batch_size
    labeled_data = DataLabel.objects.filter(
        data__project=project, training_set=current_training_set, data__irr_ind=False
    )
    labeled_data_count = labeled_data.count()
    labels_count = labeled_data.distinct("label").count()

    if current_training_set.celery_task_id != "":
        return_str = "task already running"
    elif labeled_data_count >= batch_size:
        if labels_count < project.labels.count() or project.classifier is None:
            queue = project.queue_set.get(type="normal")

            fill_queue(queue=queue, orderby="random", batch_size=batch_size)
            return_str = "random"
        else:
            task_num = tasks.send_model_task.delay(project.pk)
            current_training_set.celery_task_id = task_num
            current_training_set.save()
            return_str = "model running"
    elif profile:
        # Model is not running, check if user needs more data
        handle_empty_queue(profile, project)

        return_str = "user queue refill"
    else:
        return_str = "no trigger"

    return return_str


def train_and_save_model(project):
    """Given a project create a model, train it, and save the model pickle.

    Args:
        project: The project to start training
    Returns:
        model: A model object
    """
    if project.classifier == "logistic regression":
        clf = LogisticRegression(
            class_weight="balanced", solver="lbfgs", multi_class="multinomial"
        )
    elif project.classifier == "svm":
        clf = SVC(probability=True)
    elif project.classifier == "random forest":
        clf = RandomForestClassifier()
    elif project.classifier == "gnb":
        clf = GaussianNB()
    else:
        raise ValueError(
            "There was no valid classifier for project: " + str(project.pk)
        )
    tf_idf = load_tfidf_matrix(project.pk)

    current_training_set = project.get_current_training_set()

    # In order to train need X (tf-idf vector) and Y (label) for every labeled datum
    # Order both X and Y by upload_id_hash to ensure the tf-idf vector corresponds to the correct
    # label

    labeled_data = DataLabel.objects.filter(data__project=project)
    unique_ids = list(
        labeled_data.values_list("data__upload_id", flat=True).order_by(
            "data__upload_id_hash"
        )
    )
    labeled_values = list(
        labeled_data.values_list("label", flat=True).order_by("data__upload_id_hash")
    )

    X = [tf_idf[id] for id in unique_ids]
    Y = labeled_values
    clf.fit(X, Y)

    classes = [str(c) for c in clf.classes_]
    keys = ("precision", "recall", "f1")
    cv_predicts = cross_val_predict(clf, X, Y, cv=5)
    cv_accuracy = accuracy_score(Y, cv_predicts)
    metrics = precision_recall_fscore_support(Y, cv_predicts)
    metric_map = map(lambda x: dict(zip(classes, x)), metrics[:3])
    cv_metrics = dict(zip(keys, metric_map))

    fpath = os.path.join(
        settings.MODEL_PICKLE_PATH,
        "project_"
        + str(project.pk)
        + "_training_"
        + str(current_training_set.set_number)
        + ".pkl",
    )

    joblib.dump(clf, fpath)

    model = Model.objects.create(
        pickle_path=fpath,
        project=project,
        training_set=current_training_set,
        cv_accuracy=cv_accuracy,
        cv_metrics=cv_metrics,
    )

    return model


def predict_data(project, model):
    """Given a project and its model, predict any unlabeled data and create.

        Prediction objects for each.  There will be #label * #unlabeled_data
        predictions.  This is because we are saving the probability of each label
        for every data.

    Args:
        project: Project object
        model: Model object
    Returns:
        predictions: List of DataPrediction objects
    """
    clf = joblib.load(model.pickle_path)
    tf_idf = load_tfidf_matrix(project.pk)

    # In order to predict need X (tf-idf vector) for every unlabeled datum. Order
    # X by upload_id_hash to ensure the tf-idf vector corresponds to the correct datum
    recycle_data = RecycleBin.objects.filter(data__project=project).values_list(
        "pk", flat=True
    )
    unlabeled_data = (
        project.data_set.filter(datalabel__isnull=True)
        .exclude(pk__in=recycle_data)
        .order_by("upload_id_hash")
    )
    unique_ids = list(
        unlabeled_data.values_list("upload_id", flat=True).order_by("upload_id_hash")
    )

    # get the list of all data sorted by identifier
    X = [tf_idf[id] for id in unique_ids]
    predictions = clf.predict_proba(X)

    label_obj = [Label.objects.get(pk=label) for label in clf.classes_]

    bulk_predictions = []
    for datum, prediction in zip(unlabeled_data, predictions):
        # each prediction is an array of probabilities.  Each index in that array
        # corresponds to the label of the same index in clf.classes_
        for p, label in zip(prediction, label_obj):
            bulk_predictions.append(
                DataPrediction(
                    data=datum, model=model, label=label, predicted_probability=p
                )
            )

        # Need to crate uncertainty object so fill_queue can sort by one of the metrics
        lc = least_confident(prediction)
        ms = margin_sampling(prediction)
        e = entropy(prediction)

        DataUncertainty.objects.create(
            data=datum, model=model, least_confident=lc, margin_sampling=ms, entropy=e
        )

    prediction_objs = DataPrediction.objects.bulk_create(bulk_predictions)

    return prediction_objs


def create_tfidf_matrix(project_pk, max_df=0.995, min_df=0.005):
    """Create a TF-IDF matrix. Make sure to order the data by upload_id_hash so that we
    can sync the data up again when training the model.

    Args:
        project_pk: The pk of the project
    Returns:
        tf_idf_matrix: CSR-format tf-idf matrix
    """
    project_data = Data.objects.filter(project__pk=project_pk)
    id_list = list(
        project_data.values_list("upload_id", flat=True).order_by("upload_id_hash")
    )
    data_list = list(
        project_data.values_list("text", flat=True).order_by("upload_id_hash")
    )

    vectorizer = TfidfVectorizer(max_df=max_df, min_df=min_df, stop_words="english")
    fitted_vectorizer = vectorizer.fit(data_list)

    tf_idf_matrix = fitted_vectorizer.transform(data_list)

    new_dict = dict(
        zip(id_list, np.matrix.tolist(sparse.csr_matrix.todense(tf_idf_matrix)))
    )

    return new_dict, fitted_vectorizer


def save_tfidf_matrix(matrix, project_pk):
    """Save tf-idf matrix to persistent volume storage defined in settings as
    TF_IDF_PATH.

    Args:
        matrix: CSR-format tf-idf matrix
        project_pk: The project pk the data comes from
    Returns:
        file: The filepath to the saved matrix
    """
    fpath = os.path.join(
        settings.TF_IDF_PATH, "project_" + str(project_pk) + "_tfidf_matrix.pkl"
    )
    with open(fpath, "wb") as tfidf_file:
        pickle.dump(matrix, tfidf_file)

    return fpath


def save_tfidf_vectorizer(vectorizer, project_pk):
    """Save tf-idf matrix to persistent volume storage defined in settings as
    TF_IDF_PATH.

    Args:
        matrix: CSR-format tf-idf matrix
        project_pk: The project pk the data comes from
    Returns:
        file: The filepath to the saved matrix
    """
    fpath = os.path.join(
        settings.TF_IDF_PATH, "project_" + str(project_pk) + "_vectorizer.pkl"
    )
    with open(fpath, "wb") as tfidf_file:
        pickle.dump(vectorizer, tfidf_file)
    return fpath


def load_tfidf_matrix(project_pk):
    """Load tf-idf matrix from persistent volume, otherwise None.

    Args:
        project_pk: The project pk the data comes from
    Returns:
        matrix or None
    """
    fpath = os.path.join(
        settings.TF_IDF_PATH, "project_" + str(project_pk) + "_tfidf_matrix.pkl"
    )

    if os.path.isfile(fpath):
        with open(fpath, "rb") as file:
            return pickle.load(file)
    else:
        raise ValueError(
            "There was no tfidf matrix found for project: " + str(project_pk)
        )

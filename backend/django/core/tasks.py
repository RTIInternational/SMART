from __future__ import absolute_import

from celery import shared_task


@shared_task
def send_test_task():
    return "Test Task Complete"


@shared_task
def send_model_task(project_pk):
    """Trains, Saves, Predicts, Fills Queue."""
    from core.models import Project, TrainingSet
    from core.utils.utils_model import predict_data, train_and_save_model

    project = Project.objects.get(pk=project_pk)
    al_method = project.learning_method

    model = train_and_save_model(project)
    if al_method != "random":
        predict_data(project, model)
    TrainingSet.objects.create(
        project=project, set_number=project.get_current_training_set().set_number + 1
    )


@shared_task
def send_tfidf_creation_task(project_pk):
    """Create and Save tfidf."""
    from core.utils.utils_model import (
        create_tfidf_matrix,
        save_tfidf_matrix,
        save_tfidf_vectorizer,
    )

    tf_idf, vectorizer = create_tfidf_matrix(project_pk)
    file = save_tfidf_matrix(tf_idf, project_pk)
    save_tfidf_vectorizer(vectorizer, project_pk)

    return file


@shared_task
def send_label_embeddings_task(project_pk):
    from core.utils.util import generate_label_embeddings

    generate_label_embeddings(project_pk)


@shared_task
def send_check_and_trigger_model_task(project_pk):
    from core.models import Data
    from core.utils.utils_model import check_and_trigger_model

    datum = Data.objects.filter(project=project_pk).first()
    check_and_trigger_model(datum)

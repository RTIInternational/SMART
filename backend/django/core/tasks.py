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
    from core.utils.utils_queue import fill_queue, find_queue_length

    project = Project.objects.get(pk=project_pk)
    queue = project.queue_set.get(type="normal")
    irr_queue = project.queue_set.get(type="irr")
    al_method = project.learning_method
    batch_size = project.batch_size

    model = train_and_save_model(project)
    if al_method != "random":
        predict_data(project, model)
    TrainingSet.objects.create(
        project=project, set_number=project.get_current_training_set().set_number + 1
    )

    # Determine if queue size has changed (num_coders changed) and re-fill queue
    num_coders = len(project.projectpermissions_set.all()) + 1
    q_length = find_queue_length(batch_size, num_coders)
    if q_length != queue.length:
        queue.length = q_length
        queue.save()

    fill_queue(
        queue,
        irr_queue=irr_queue,
        orderby=al_method,
        irr_percent=project.percentage_irr,
        batch_size=batch_size,
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
def send_check_and_trigger_model_task(project_pk):
    from core.models import Data
    from core.utils.utils_model import check_and_trigger_model

    datum = Data.objects.filter(project=project_pk).first()
    check_and_trigger_model(datum)

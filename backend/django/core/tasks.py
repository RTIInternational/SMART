from __future__ import absolute_import
from celery import shared_task
import math


@shared_task
def send_test_task():
    return 'Test Task Complete'


@shared_task
def send_model_task(project_pk):
    """Trains, Saves, Predicts, Fills Queue"""
    from core.models import Project, Data, Label, TrainingSet
    from core.util import train_and_save_model, predict_data, fill_queue, find_queue_length

    project = Project.objects.get(pk=project_pk)
    queue = project.queue_set.get(type="normal")
    irr_queue = project.queue_set.get(type="irr")

    model = train_and_save_model(project)
    predictions = predict_data(project, model)
    new_training_set = TrainingSet.objects.create(project=project,
                                                  set_number=project.get_current_training_set().set_number + 1)

    # Determine if queue size has changed (num_coders changed) and re-fill queue
    batch_size = project.batch_size
    num_coders = len(project.projectpermissions_set.all()) + 1
    q_length = find_queue_length(batch_size, num_coders)

    if q_length != queue.length:
        queue.length = q_length
        queue.save()

    al_method = project.learning_method
    fill_queue(queue, irr_queue=irr_queue, orderby=al_method,
               irr_percent=project.percentage_irr, batch_size=batch_size)


@shared_task
def send_tfidf_creation_task(response, project_pk):
    """Create and Save tfidf"""
    from core.util import create_tfidf_matrix, save_tfidf_matrix, save_tfidf_vectorizer
    from core.models import Data

    # since data is serialized objects need to validate, then retrieve the actual objects
    hashes = [od['hash'] for od in response]
    data = Data.objects.filter(hash__in=hashes)

    tf_idf, vectorizer = create_tfidf_matrix(data, project_pk)
    file = save_tfidf_matrix(tf_idf, project_pk)
    save_tfidf_vectorizer(vectorizer, project_pk)

    return file


@shared_task
def send_check_and_trigger_model_task(project_pk):
    from core.util import check_and_trigger_model
    from core.models import Data

    datum = Data.objects.filter(project=project_pk).first()
    check_and_trigger_model(datum)

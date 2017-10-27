from __future__ import absolute_import
from celery import shared_task


@shared_task
def send_test_task():
    return 'Test Task Complete'

@shared_task
def send_model_task(project_pk):
    """Trains, Saves, Predicts, Fills Queue"""
    from core.models import Project, Data, Label, TrainingSet
    from core.util import train_and_save_model, predict_data, fill_queue

    project = Project.objects.get(pk=project_pk)

    model = train_and_save_model(project)
    predictions = predict_data(project, model)
    new_training_set = TrainingSet.objects.create(project=project,
                               set_number=project.get_current_training_set().set_number+1)
    fill_queue(project.queue_set.get(), 'least confident')

@shared_task
def send_tfidf_creation_task(data, project_pk):
    """Create and Save tfidf"""
    from core.util import create_tfidf_matrix, save_tfidf_matrix

    tf_idf = create_tfidf_matrix(data)
    file = save_tfidf_matrix(tf_idf, project_pk)

    return file
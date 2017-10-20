from __future__ import absolute_import
from celery import shared_task


@shared_task
def send_test_task():
    return 'Test Task Complete'

@shared_task
def send_model_task(project_pk, prefix_dir=None):
    """Trains, Saves, Predicts, Fills Queue"""
    from core.models import Project, Data, Label
    from core.util import train_and_save_model, predict_data, fill_queue

    project = Project.objects.get(pk=project_pk)

    model = train_and_save_model(project, prefix_dir)
    predictions = predict_data(project, model, prefix_dir)
    fill_queue(project.queue_set.get(), 'least confident')
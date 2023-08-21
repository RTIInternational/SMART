import random
from core import tasks
from core.utils.utils_annotate import get_assignments, label_data
from core.utils.utils_queue import fill_queue


def label_project(project, profile, num_labels):
    labels = project.labels.all()

    current_training_set = project.get_current_training_set()

    assignments = get_assignments(profile, project, num_labels)
    for i in range(min(len(labels), len(assignments))):
        label_data(labels[i], assignments[i], profile, random.randint(0, 25))

    for assignment in assignments[len(labels) :]:
        label_data(random.choice(labels), assignment, profile, random.randint(0, 25))

    task_num = tasks.send_model_task.apply(args=[project.pk])
    current_training_set.celery_task_id = task_num
    current_training_set.save()

    fill_queue(
        project.queue_set.get(type="normal"),
        irr_queue=project.queue_set.get(type="irr"),
        orderby="random",
        batch_size=project.batch_size,
        irr_percent=project.percentage_irr,
    )

from test.util import read_test_data_backend
from core import tasks
from core.models import (
    ExternalDatabase,
    Label,
    Project,
    ProjectPermissions,
    TrainingSet,
)
from core.utils.util import add_data, save_data_file
from core.utils.utils_queue import add_queue, fill_queue, find_queue_length


# multi_user_project = seed_project(
#     creator=root,
#     name="Three User Project",
#     description="This is a project that is coded by three different users.  No labels were in the data file to begin with.",
#     data_file="./core/data/test_files/test_no_labels.csv",
#     label_list=["about cats", "not about cats", "unclear"],
#     perm_list=[user1, test_user],
#     classifier="logistic regression",
def seed_project(
    creator, name, description, data_file, label_list, perm_list, classifier
):
    """Creates Project with related objects: TrainingSet, ExternalDatabase, Labels, and ProjectPermissions"""
    project = Project.objects.create(
        name=name, description=description, creator=creator, classifier=classifier
    )

    TrainingSet.objects.create(project=project, set_number=0)

    ExternalDatabase.objects.create(project=project, env_file="", database_type="none")

    for name in label_list:
        Label.objects.create(name=name, project=project)

    for perm in perm_list:
        ProjectPermissions.objects.create(
            profile=perm, project=project, permission="CODER"
        )

    batch_size = 10 * len(label_list)
    project.batch_size = batch_size
    project.save()

    num_coders = len(perm_list) + 1
    queue_length = find_queue_length(batch_size, num_coders)
    queue = add_queue(project=project, length=queue_length, type="normal")

    # Data
    f_data = read_test_data_backend(file=data_file)
    data_length = len(f_data)

    # Create admin and irr queues
    add_queue(project=project, length=data_length, type="admin")
    irr_queue = add_queue(project=project, length=2000000, type="irr")
    new_df = add_data(project, f_data)
    fill_queue(
        queue,
        irr_queue=irr_queue,
        orderby="random",
        batch_size=batch_size,
        irr_percent=project.percentage_irr,
    )
    save_data_file(new_df, project.pk)

    tasks.send_tfidf_creation_task.apply(args=[project.pk])
    tasks.send_check_and_trigger_model_task.apply(args=[project.pk])

    return project

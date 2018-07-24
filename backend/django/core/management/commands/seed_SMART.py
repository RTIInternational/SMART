from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import Profile, Project, Label, ProjectPermissions, TrainingSet
from core.util import (add_data, find_queue_length, add_queue, get_assignments,
                       label_data, check_and_trigger_model, fill_queue, save_data_file)
from core.views.frontend import upload_data
from core.serializers import DataSerializer
from core import tasks

from test.util import read_test_data_backend

import random

AuthUser = get_user_model()

def seed_users():
    root_auth = AuthUser.objects.create_user(username='root', password='password555', email='test@test.com')
    user1_auth = AuthUser.objects.create_user(username='user1', password='password555', email='test@test.com')
    test_user_auth = AuthUser.objects.create_user(username='test_user', password='password555', email='test@test.com')

    return Profile.objects.get(user=root_auth), Profile.objects.get(user=user1_auth), Profile.objects.get(user=test_user_auth)

def seed_project(creator, name, description, data_file, label_list, perm_list):
    project = Project.objects.create(name=name,
        description=description,
        creator=creator
    )

    training_set = TrainingSet.objects.create(project=project, set_number=0)

    labels = []
    for name in label_list:
        labels.append(Label.objects.create(name=name, project=project))

    permissions = []
    for perm in perm_list:
        permissions.append(ProjectPermissions.objects.create(profile=perm, project=project, permission='CODER'))

    batch_size = 10 * len(labels)
    num_coders = len(permissions) + 1
    q_length = find_queue_length(batch_size, num_coders)

    queue = add_queue(project=project, length=q_length, type="normal")


    # Data
    f_data = read_test_data_backend(file=data_file)
    data_length = len(f_data)
    admin_queue = add_queue(project=project,length=data_length, type="admin")
    irr_queue = add_queue(project=project,length=data_length, type="irr")
    data_objs = add_data(project, f_data)
    fill_queue(queue, irr_queue = irr_queue, orderby='random', batch_size = batch_size)
    save_data_file(f_data, project.pk)

    tasks.send_tfidf_creation_task.apply(args=[DataSerializer(data_objs, many=True).data, project.pk])
    tasks.send_check_and_trigger_model_task.apply(args=[project.pk])

    return project

def label_project(project, profile, num_labels):
    labels = project.labels.all()

    current_training_set = project.get_current_training_set()

    assignments = get_assignments(profile, project, num_labels)
    for i in range(min(len(labels), len(assignments))):
        label_data(labels[i], assignments[i], profile, random.randint(0,25))
    for assignment in assignments[len(labels):]:
        label_data(random.choice(labels), assignment, profile, random.randint(0,25))

    task_num = tasks.send_model_task.apply(args=[project.pk])
    current_training_set.celery_task_id = task_num
    current_training_set.save()

class Command(BaseCommand):
    help = 'Seeds the SMART App with a few users, projects, and labels'

    def handle(self, *args, **options):
        print('Seeding the database with some test data...')
        with transaction.atomic():
            print('Test users...')
            root, user1, test_user = seed_users()

            print('Test projects...')
            root_project = seed_project(creator=root,
                name='Root Only Project',
                description="This is a project for only the root user. The root user is the creator.  This project's data file has labels.",
                data_file='./core/data/test_files/test_some_labels.csv',
                label_list=['FAVOR', 'AGAINST', 'NONE'],
                perm_list=[]
            )
            multi_user_project = seed_project(creator=root,
                name='Three User Project',
                description="This is a project that is coded by three different users.  No labels were in the data file to begin with.",
                data_file='./core/data/test_files/test_no_labels.csv',
                label_list=['Good', 'Bad'],
                perm_list=[user1, test_user]
            )
            no_data_project = seed_project(creator=root,
                name='No Label Project',
                description="This project has no labels, all charts should say No Data Available",
                data_file='./core/data/test_files/test_no_labels.csv',
                label_list=['Good', 'Bad', 'Neutral'],
                perm_list=[]
            )

            print('Test labels...')
            for i in range(3):
                label_project(root_project, root, root_project.labels.count()*10)
            label_project(multi_user_project, root, multi_user_project.labels.count()*10)
            label_project(multi_user_project, user1, multi_user_project.labels.count()*10)
            label_project(multi_user_project, test_user, multi_user_project.labels.count()*10)

        print('Finished seeding database.')

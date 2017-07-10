from __future__ import absolute_import
from celery import shared_task
from celery.exceptions import Ignore
import csv

from .models import Project, Data, Label

@shared_task
def test():
    return print("Test Task run")

@shared_task(bind=True)
def seed_data(self):
    project, created = Project.objects.get_or_create(name='seed-data')
    if not created:
        self.update_state(state='FAILURE', meta={'message': 'seed-data Project Already Exists', 'project.pk': project.pk})
        raise Ignore()
    else:
        with open('./core/data/SemEval-2016-Task6/train-feminism.csv') as inf:
            reader = csv.DictReader(inf)
            sample_data = []
            for row in reader:
                data = Data(text=row['Tweet'], project=project)
                sample_data.append(data) 
            dataset = Data.objects.bulk_create(sample_data)
        for label in ['AGAINST', 'FAVOR', 'NONE']:
            Label.objects.create(name=label, project=project)
        return {'message': 'Project Data Seeded.', 'project.pk': project.pk}
from django.db import models
from django.conf import settings

class User(models.Model):
    # Link to the auth user, since we're basically just extending it
    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL)
    labels = models.ManyToManyField(
        'Data', related_name='labelers', through='DataLabel'
    )

class Project(models.Model):
    pass

class Model(models.Model):
    pickle_path = models.FilePathField(path=settings.MODEL_PICKLE_PATH)
    project = models.ForeignKey('Project')
    predictions = models.ManyToManyField(
        'Data', related_name='models', through='DataPrediction'
    )

class Data(models.Model):
    text = models.TextField()
    project = models.ForeignKey('Project')

class DataLabel(models.Model):
    class Meta:
        unique_together = (('data', 'user'))
    data = models.ForeignKey('Data')
    user = models.ForeignKey('User')
    label = models.TextField()

class DataPrediction(models.Model):
    class Meta:
        unique_together = (('data', 'model'))
    data = models.ForeignKey('Data')
    model = models.ForeignKey('Model')
    predicted_class = models.TextField()
    predicted_probability = models.FloatField()

class Queue(models.Model):
    user = models.ForeignKey('User', blank=True)
    project = models.ForeignKey('Project')
    length = models.IntegerField()
    data = models.ManyToManyField(
        'Data', related_name='queues', through='DataQueue'
    )

class DataQueue(models.Model):
    class Meta:
        unique_together = (('queue', 'data'))
    queue = models.ForeignKey('Queue')
    data = models.ForeignKey('Data')

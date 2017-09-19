from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

class User(models.Model):
    # Link to the auth user, since we're basically just extending it
    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL)
    labeled_data = models.ManyToManyField(
        'Data', related_name='labelers', through='DataLabel'
    )

class Project(models.Model):
    name = models.TextField()
    description = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL)

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})

class ProjectPermissions(models.Model):
    class Meta:
        unique_together = (('user', 'project'))
    PERM_CHOICES = (
        ('ADMIN', 'Admin'),
        ('CODER', 'Coder'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    project = models.ForeignKey('Project')
    permission = models.CharField(max_length=5,choices=PERM_CHOICES)

class Model(models.Model):
    pickle_path = models.TextField()
    project = models.ForeignKey('Project')
    predictions = models.ManyToManyField(
        'Data', related_name='models', through='DataPrediction'
    )

class Data(models.Model):
    text = models.TextField()
    hash = models.CharField(max_length=128)
    project = models.ForeignKey('Project')

class Label(models.Model):
    name = models.TextField()
    project = models.ForeignKey('Project')

class DataLabel(models.Model):
    class Meta:
        unique_together = (('data', 'user'))
    data = models.ForeignKey('Data')
    user = models.ForeignKey('User')
    label = models.ForeignKey('Label')

class DataPrediction(models.Model):
    class Meta:
        unique_together = (('data', 'model'))
    data = models.ForeignKey('Data')
    model = models.ForeignKey('Model')
    predicted_class = models.TextField()
    predicted_probability = models.FloatField()

class Queue(models.Model):
    user = models.ForeignKey('User', blank=True, null=True)
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

class AssignedData(models.Model):
    class Meta:
        unique_together = (('user', 'queue'), ('user', 'data'))
    user = models.ForeignKey('User')
    data = models.ForeignKey('Data')
    queue = models.ForeignKey('Queue')
    assigned_timestamp = models.DateTimeField(default = timezone.now)

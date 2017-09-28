from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(models.Model):
    # Link to the auth user, since we're basically just extending it
    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL)
    labeled_data = models.ManyToManyField(
        'Data', related_name='labelers', through='DataLabel'
    )

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user(sender, instance, created, **kwargs):
    if created:
        User.objects.create(auth_user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user(sender, instance, **kwargs):
    instance.user.save()

class Project(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True)
    creator = models.ForeignKey('User')

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})

class ProjectPermissions(models.Model):
    class Meta:
        unique_together = (('user', 'project'))
    PERM_CHOICES = (
        ('ADMIN', 'Admin'),
        ('CODER', 'Coder'),
    )
    user = models.ForeignKey('User')
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

    def __str__(self):
        return self.text

class Label(models.Model):
    name = models.TextField()
    project = models.ForeignKey('Project', related_name='labels', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

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

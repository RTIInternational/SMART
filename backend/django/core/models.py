from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    # Link to the auth user, since we're basically just extending it
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    labeled_data = models.ManyToManyField(
        'Data', related_name='labelers', through='DataLabel'
    )

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user(sender, instance, **kwargs):
    instance.profile.save()

class Project(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True)
    creator = models.ForeignKey('Profile')

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})

    def get_current_training_set(self):
        try:
            return self.trainingset_set.all().order_by('-set_number')[0]
        except IndexError:
            return None

class ProjectPermissions(models.Model):
    class Meta:
        unique_together = (('profile', 'project'))
    PERM_CHOICES = (
        ('ADMIN', 'Admin'),
        ('CODER', 'Coder'),
    )
    profile = models.ForeignKey('Profile')
    project = models.ForeignKey('Project')
    permission = models.CharField(max_length=5,choices=PERM_CHOICES)

class Model(models.Model):
    pickle_path = models.TextField()
    project = models.ForeignKey('Project')
    training_set = models.ForeignKey('TrainingSet')
    predictions = models.ManyToManyField(
        'Data', related_name='models', through='DataPrediction'
    )

class Data(models.Model):
    text = models.TextField()
    hash = models.CharField(max_length=128)
    project = models.ForeignKey('Project')
    df_idx = models.IntegerField()

    def __str__(self):
        return self.text

class Label(models.Model):
    class Meta:
        unique_together = (('name', 'project'))
    name = models.TextField()
    project = models.ForeignKey('Project', related_name='labels', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class DataLabel(models.Model):
    class Meta:
        unique_together = (('data', 'profile'))
    data = models.ForeignKey('Data')
    profile = models.ForeignKey('Profile')
    label = models.ForeignKey('Label')
    training_set = models.ForeignKey('TrainingSet')
    time_to_label = models.IntegerField(null=True)

class DataPrediction(models.Model):
    class Meta:
        unique_together = (('data', 'model', 'label'))
    data = models.ForeignKey('Data')
    model = models.ForeignKey('Model')
    label = models.ForeignKey('Label')
    predicted_probability = models.FloatField()

class DataUncertainty(models.Model):
    class Meta:
        unique_together = (('data', 'model'))
    data = models.ForeignKey('Data')
    model = models.ForeignKey('Model')
    least_confident = models.FloatField()
    margin_sampling = models.FloatField()
    entropy = models.FloatField()

class Queue(models.Model):
    profile = models.ForeignKey('Profile', blank=True, null=True)
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
        unique_together = (('profile', 'queue', 'data'))
    profile = models.ForeignKey('Profile')
    data = models.ForeignKey('Data')
    queue = models.ForeignKey('Queue')
    assigned_timestamp = models.DateTimeField(default = timezone.now)

class TrainingSet(models.Model):
    project = models.ForeignKey('Project')
    set_number = models.IntegerField()
    celery_task_id = models.TextField(blank=True)

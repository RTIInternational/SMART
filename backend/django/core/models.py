from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField

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
    codebook_file = models.TextField(default='')
    batch_size = models.IntegerField(default=30)
    #####Advanced options#####
    #the current options are 'random', 'least confident', 'entropy', and 'margin sampling'
    ACTIVE_L_CHOICES = [
        ("least confident","By Uncertainty using Least Confident"),
        ("margin sampling","By Uncertainty using the Margin"),
        ("entropy","By Uncertainty using Entropy"),
        ("random","Randomly (No Active Learning)")
    ]

    CLASSIFIER_CHOICES = [
        ("logistic_regression","Logistic Regression (default)"),
        ("svm","Support Vector Machine (warning: slower for large datasets)"),
        ("random_forest","Random Forest"),
        ("gnb","Gaussian Naive Bayes")
    ]

    learning_method = models.CharField(max_length = 15, default='least confident', choices=ACTIVE_L_CHOICES)
    classifier = models.CharField(max_length = 19, default="logistic_regression", choices = CLASSIFIER_CHOICES, null=True)

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})

    def get_current_training_set(self):
        try:
            return self.trainingset_set.all().order_by('-set_number')[0]
        except IndexError:
            return None

    def admin_count(self):
        return self.projectpermissions_set.all().filter(permission='ADMIN').count()

    def coder_count(self):
        return self.projectpermissions_set.all().filter(permission='CODER').count()

    def labeled_data_count(self):
        return self.data_set.all().filter(datalabel__isnull=False).count()

    def has_classifier(self):
        if self.classifier is not None:
            return 1
        else:
            return 0
            
    def has_model(self):
        if self.model_set.count() > 0:
            return True
        else:
            return False

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
    cv_accuracy = models.FloatField()
    cv_metrics = JSONField()
    predictions = models.ManyToManyField(
        'Data', related_name='models', through='DataPrediction'
    )

class Data(models.Model):
    class Meta:
        unique_together = (('hash', 'upload_id_hash', 'project'))
    text = models.TextField()
    hash = models.CharField(max_length=128)
    project = models.ForeignKey('Project')
    upload_id = models.CharField(max_length=128)
    upload_id_hash = models.CharField(max_length=128)

    def __str__(self):
        return self.text

class Label(models.Model):
    class Meta:
        unique_together = (('name', 'project'))
    name = models.TextField()
    project = models.ForeignKey('Project', related_name='labels', on_delete=models.CASCADE)
    description = models.TextField(blank=True)

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
    timestamp = models.DateTimeField(null=True, default= None)

class LabelChangeLog(models.Model):
    project = models.ForeignKey('Project')
    data = models.ForeignKey('Data')
    profile = models.ForeignKey('Profile')
    old_label = models.TextField()
    new_label = models.TextField()
    change_timestamp = models.DateTimeField(null=True, default= None)

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
    admin = models.BooleanField(default=False)
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

class RecycleBin(models.Model):
    data = models.ForeignKey('Data')
    timestamp = models.DateTimeField(default = timezone.now)

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone


class Profile(models.Model):
    # Link to the auth user, since we're basically just extending it
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    labeled_data = models.ManyToManyField(
        "Data", related_name="labelers", through="DataLabel"
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
    creator = models.ForeignKey("Profile")
    percentage_irr = models.FloatField(
        default=10.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    num_users_irr = models.IntegerField(default=2, validators=[MinValueValidator(2)])
    codebook_file = models.TextField(default="")
    batch_size = models.IntegerField(default=30)

    use_explicit_ind = models.BooleanField(default=False)
    """ Advanced options """
    # the current options are 'random',
    # 'least confident', 'entropy', and 'margin sampling'
    ACTIVE_L_CHOICES = [
        ("least confident", "By Uncertainty using Least Confident"),
        ("margin sampling", "By Uncertainty using the Margin"),
        ("entropy", "By Uncertainty using Entropy"),
        ("random", "Randomly (No Active Learning)"),
    ]

    CLASSIFIER_CHOICES = [
        ("logistic regression", "Logistic Regression (default)"),
        ("svm", "Support Vector Machine (warning: slower for large datasets)"),
        ("random forest", "Random Forest"),
        ("gnb", "Gaussian Naive Bayes"),
    ]

    learning_method = models.CharField(
        max_length=15, default="least confident", choices=ACTIVE_L_CHOICES
    )
    classifier = models.CharField(
        max_length=19,
        default="logistic regression",
        choices=CLASSIFIER_CHOICES,
        null=True,
    )

    def get_absolute_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.pk})

    def get_current_training_set(self):
        try:
            return self.trainingset_set.all().order_by("-set_number")[0]
        except IndexError:
            return None

    def admin_count(self):
        return self.projectpermissions_set.all().filter(permission="ADMIN").count()

    def coder_count(self):
        return self.projectpermissions_set.all().filter(permission="CODER").count()

    def labeled_data_count(self):
        return (
            self.data_set.all().filter(datalabel__isnull=False, irr_ind=False).count()
        )

    def excluded_data_count(self):
        return self.data_set.all().filter(recyclebin__isnull=False).count()

    def irr_data_count(self):
        return (
            self.data_set.all().filter(irrlog__isnull=False).count()
            + self.data_set.all().filter(datalabel__isnull=False, irr_ind=True).count()
        )

    def has_model(self):
        if self.model_set.count() > 0:
            return True
        else:
            return False


class ProjectPermissions(models.Model):
    class Meta:
        unique_together = ("profile", "project")

    PERM_CHOICES = (("ADMIN", "Admin"), ("CODER", "Coder"))
    profile = models.ForeignKey("Profile")
    project = models.ForeignKey("Project")
    permission = models.CharField(max_length=5, choices=PERM_CHOICES)


class Model(models.Model):
    pickle_path = models.TextField()
    project = models.ForeignKey("Project")
    training_set = models.ForeignKey("TrainingSet")
    cv_accuracy = models.FloatField()
    cv_metrics = JSONField()
    predictions = models.ManyToManyField(
        "Data", related_name="models", through="DataPrediction"
    )


class Data(models.Model):
    class Meta:
        unique_together = ("hash", "upload_id_hash", "project")

    text = models.TextField()
    hash = models.CharField(max_length=128)
    project = models.ForeignKey("Project")
    irr_ind = models.BooleanField(default=False)
    upload_id = models.CharField(max_length=128)
    upload_id_hash = models.CharField(max_length=128)
    explicit_ind = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Label(models.Model):
    class Meta:
        unique_together = ("name", "project")

    name = models.TextField()
    project = models.ForeignKey(
        "Project", related_name="labels", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class IRRLogManager(models.Manager):
    def unexcluded(self):
        """Return the IRRLog objects which are not in the recyclebin."""
        return self.filter(data__recyclebin__isnull=True)

    def skipped(self):
        """Return the IRRLog objects for skipped data."""
        return self.filter(label__isnull=True, data__recyclebin__isnull=True)


class IRRLog(models.Model):
    class Meta:
        unique_together = ("data", "profile")

    data = models.ForeignKey("Data")
    profile = models.ForeignKey("Profile")
    label = models.ForeignKey("Label", null=True)
    label_reason = models.TextField(null=True, default="")
    timestamp = models.DateTimeField(null=True, default=None)
    time_to_label = models.IntegerField(null=True)
    objects = IRRLogManager()


class DataLabelManager(models.Manager):
    def finalized(self):
        """Return the dataLabel objects which are not skipped, involved in IRR, or in
        the recyclebin."""
        return self.filter(
            data__irr_ind=False, was_skipped=False, data__recyclebin__isnull=True
        ).exclude(data__dataqueue__queue__type="admin")

    def finalized_or_irr(self):
        """Return the dataLabel objects which are not skipped or in the recyclebin but
        could be IRR."""
        return self.filter(was_skipped=False, data__recyclebin__isnull=True).exclude(
            data__dataqueue__queue__type="admin"
        )

    def irr(self):
        """Return the dataLabel objects which are not in the recyclebin and are IRR."""
        return self.filter(
            data__irr_ind=True, was_skipped=False, data__recyclebin__isnull=True
        ).exclude(data__dataqueue__queue__type="admin")

    def unexcluded(self):
        """return the DataLabel objects not in the recycleBin."""
        return self.filter(data__recyclebin__isnull=True)


class DataLabel(models.Model):
    class Meta:
        unique_together = ("data", "profile")

    data = models.ForeignKey("Data")
    profile = models.ForeignKey("Profile")
    label = models.ForeignKey("Label")
    label_reason = models.TextField(null=True, default="")
    training_set = models.ForeignKey("TrainingSet")
    time_to_label = models.IntegerField(null=True)
    timestamp = models.DateTimeField(null=True, default=None)
    was_skipped = models.BooleanField(default=False)
    objects = DataLabelManager()


class LabelChangeLog(models.Model):
    project = models.ForeignKey("Project")
    data = models.ForeignKey("Data")
    profile = models.ForeignKey("Profile")
    old_label = models.TextField()
    new_label = models.TextField()
    change_timestamp = models.DateTimeField(null=True, default=None)


class DataPrediction(models.Model):
    class Meta:
        unique_together = ("data", "model", "label")

    data = models.ForeignKey("Data")
    model = models.ForeignKey("Model")
    label = models.ForeignKey("Label")
    predicted_probability = models.FloatField()


class DataUncertainty(models.Model):
    class Meta:
        unique_together = ("data", "model")

    data = models.ForeignKey("Data")
    model = models.ForeignKey("Model")
    least_confident = models.FloatField()
    margin_sampling = models.FloatField()
    entropy = models.FloatField()


class Queue(models.Model):
    profile = models.ForeignKey("Profile", blank=True, null=True)
    project = models.ForeignKey("Project")
    QUEUE_TYPES = (("admin", "Admin"), ("irr", "IRR"), ("normal", "Normal"))
    type = models.CharField(max_length=6, default="normal", choices=QUEUE_TYPES)
    length = models.IntegerField()
    data = models.ManyToManyField("Data", related_name="queues", through="DataQueue")


class DataQueue(models.Model):
    class Meta:
        unique_together = ("queue", "data")

    queue = models.ForeignKey("Queue")
    data = models.ForeignKey("Data")


class AssignedData(models.Model):
    class Meta:
        unique_together = ("profile", "queue", "data")

    profile = models.ForeignKey("Profile")
    data = models.ForeignKey("Data")
    queue = models.ForeignKey("Queue")
    assigned_timestamp = models.DateTimeField(default=timezone.now)


class TrainingSet(models.Model):
    project = models.ForeignKey("Project")
    set_number = models.IntegerField()
    celery_task_id = models.TextField(blank=True)


class RecycleBin(models.Model):
    data = models.ForeignKey("Data")
    exclude_reason = models.TextField(null=True, default="")
    timestamp = models.DateTimeField(default=timezone.now)


class AdminProgress(models.Model):
    project = models.ForeignKey("Project")
    profile = models.ForeignKey("Profile")
    timestamp = models.DateTimeField(default=timezone.now)


class MetaData(models.Model):
    data = models.OneToOneField(Data, on_delete=models.CASCADE, primary_key=True)
    title = models.TextField(null=True, blank=True)

    created_date = models.DateTimeField(null=True)
    username = models.TextField(blank=True, null=True)
    url = models.URLField(null=True, max_length=500)
    user_url = models.URLField(null=True, max_length=500)

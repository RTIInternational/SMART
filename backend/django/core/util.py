import random
import redis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.externals import joblib
from scipy import sparse
import os

from django.db import transaction, connection
from django.db.models import Count, Value, IntegerField, F
from django.contrib.auth import get_user_model
from django.conf import settings

from core.models import (Project, Data, Queue, DataQueue, Profile,
                         AssignedData, DataLabel)


# TODO: Divide these functions into a public/private API when we determine
#  what functionality is needed by the frontend.  This file is a little
#  intimidating to sort through at the moment.

def create_profile(username, password, email):
    '''
    Create a user with the given attributes.
    Create a user in Django's authentication model and
    link it to our own project user model.
    '''
    user = get_user_model().objects.create(
        username=username,
        password=password,
        email=email)

    return Profile.objects.get(user=user)


def iter_sample(iterable, sample_len):
    '''
    Sample the given number of items from the given iterable without
    loading all objects in the iterable into memory.
    Based on this: https://stackoverflow.com/a/12583436/2612566
    '''
    results = []
    iterator = iter(iterable)

    # Fill in the first sample_len elements
    try:
        for _ in range(sample_len):
            results.append(next(iterator))
    except StopIteration:
        raise ValueError("Sample larger than population.")

    # Randomize their positions
    random.shuffle(results)

    # At a decreasing rate, replace random items
    for i, v in enumerate(iterator, sample_len):
        r = random.randint(0, i)
        if r < sample_len:
            results[r] = v

    return results


def init_redis_queues():
    '''
    Create a redis queue for each queue in the database and fill it with
    the data linked to the queue.

    This will remove any existing queue keys from redis and re-populate the redis
    db to be in sync with the postgres state
    '''
    # Use a pipeline to reduce back-and-forth with the server
    pipeline = settings.REDIS.pipeline(transaction=False)

    existing_keys = [key for key in settings.REDIS.scan_iter('queue:*')]
    if len(existing_keys) > 0:
        # We'll get an error if we try to del without any keys
        pipeline.delete(*existing_keys)

    assigned_data_ids = set((d.data_id for d in AssignedData.objects.all()))
    for queue in Queue.objects.all():
        data_ids = ['data:'+str(d.pk) for d in queue.data.all() if d.pk not in assigned_data_ids]
        if len(data_ids) > 0:
            # We'll get an error if we try to lpush without any data
            pipeline.lpush('queue:'+str(queue.pk), *data_ids)

    pipeline.execute()


def create_project(name, creator):
    '''
    Create a project with the given name and creator.
    '''
    return Project.objects.create(name=name, creator=creator)


def add_data(project, data):
    '''
    Add data to an existing project.  Data should be an array of strings.
    '''
    bulk_data = (Data(text=d, project=project) for d in data)
    Data.objects.bulk_create(bulk_data)


def add_queue(project, length, profile=None):
    '''
    Add a queue of the given length to the given project.  If a profile is provided,
    assign the queue to that profile.

    Return the created queue.
    '''
    return Queue.objects.create(length=length, project=project, profile=profile)


def fill_queue(queue):
    '''
    Fill a queue with unlabeled, unassigned data randomly selected from
    the queue's project. The queue doesn't need to be empty.

    If there isn't enough data left to fill the queue, use all the
    data available.

    TODO: Extend to use a model to fill the queue, when one has been trained
    for the queue's project.
    '''
    data_filters = {
        'project': queue.project,
        'labelers': None,
        'queues': None
    }

    eligible_data = Data.objects.filter(**data_filters)

    cte_sql, cte_params = eligible_data.query.sql_with_params()
    sample_size_sql, sample_size_params = (Queue.objects.filter(pk=queue.pk)
                                            .annotate(
                                                sample_size=F('length') - Count('data'))
                                            .values('sample_size')
                                            .query.sql_with_params())

    sql = """
    WITH eligible_data AS (
        {cte_sql}
    )
    INSERT INTO {dataqueue_table}
      ({dataqueue_data_id_col}, {dataqueue_queue_id_col})
    SELECT
        eligible_data.{data_pk_col},
        {queue_id}
    FROM
        eligible_data
    ORDER BY random()
    LIMIT ({sample_size_sql});
    """.format(
        cte_sql=cte_sql,
        dataqueue_table=DataQueue._meta.db_table,
        dataqueue_data_id_col=DataQueue._meta.get_field('data').column,
        dataqueue_queue_id_col=DataQueue._meta.get_field('queue').column,
        data_pk_col=Data._meta.pk.name,
        queue_id=queue.pk,
        sample_size_sql=sample_size_sql)

    with connection.cursor() as c:
        c.execute(sql, (*cte_params, *sample_size_params))

    data_ids = ['data:'+str(d.pk) for d in queue.data.all()]
    settings.REDIS.lpush('queue:'+str(queue.pk), *data_ids)


def pop_first_nonempty_queue(project, profile=None):
    '''
    Determine which queues are eligible to be popped (and in what order)
    and pass them into redis to have the first nonempty one popped.
    Return a (queue, data item) tuple if one was found; return a (None, None)
    tuple if not.
    '''
    if profile is not None:
        # Use priority to ensure we set profile queues above project queues
        # in the resulting list; break ties by pk
        profile_queues = project.queue_set.filter(profile=profile)
    else:
        profile_queues = Queue.objects.none()
    profile_queues = profile_queues.annotate(priority=Value(1, IntegerField()))

    project_queues = (project.queue_set.filter(profile=None)
                      .annotate(priority=Value(2, IntegerField())))

    eligible_queue_ids = ['queue:'+str(queue.pk) for queue in
                          (profile_queues.union(project_queues)
                           .order_by('priority', 'pk'))]

    if len(eligible_queue_ids) == 0:
        return (None, None)

    # Use a custom Lua script here to find the first nonempty queue atomically
    # and pop its first item.  If all queues are empty, return nil.
    script = settings.REDIS.register_script('''
    for _, k in pairs(KEYS) do
      local m = redis.call('LPOP', k)
      if m then
        return {k, m}
      end
    end
    return nil
    ''')

    result = script(keys=eligible_queue_ids)

    if result is None:
        return (None, None)
    else:
        queue_id = result[0].decode().split(':')[1]
        data_id = result[1].decode().split(':')[1]
        return (Queue.objects.filter(pk=queue_id).get(),
                Data.objects.filter(pk=data_id).get())


def pop_queue(queue):
    '''
    Remove a datum from the given queue (in redis and the database)
    and return it.

    Returns None and does nothing if the queue is empty.

    Client code should prefer pop_first_nonempty_queue() if the
    intent is to pop the first nonempty queue, as it avoids
    concurrency issues.
    '''
    # Redis first, since this op is guaranteed to be atomic
    data_id = settings.REDIS.rpop('queue:'+str(queue.pk))

    if data_id is None:
        return None
    else:
        data_id = data_id.decode().split(':')[1]

    data_obj = Data.objects.filter(pk=data_id).get()

    return data_obj


def get_nonempty_queue(project, profile=None):
    '''
    Return the first nonempty queue for the given project and
    (optionally) profile.

    Client code should prefer pop_first_nonempty_queue() if the
    intent is to pop the first nonempty queue, as it avoids
    concurrency issues.
    '''
    first_nonempty_queue = None

    # Only check for profile queues if we were passed a profile
    if profile is not None:
        nonempty_profile_queues = (project.queue_set
                                .filter(profile=profile)
                                .annotate(
                                    data_count=Count('data'))
                                .filter(data_count__gt=0))

        if len(nonempty_profile_queues) > 0:
            first_nonempty_queue = nonempty_profile_queues.first()

    # If we didn't find a profile queue, check project queues
    if first_nonempty_queue is None:
        nonempty_queues = (project.queue_set
                           .filter(profile=None)
                           .annotate(
                               data_count=Count('data'))
                           .filter(data_count__gt=0))

        if len(nonempty_queues) > 0:
            first_nonempty_queue = nonempty_queues.first()

    return first_nonempty_queue


def assign_datum(profile, project):
    '''
    Given a profile and project, figure out which queue to pull from;
    then pop a datum off that queue and assign it to the profile.
    '''
    with transaction.atomic():
        queue, datum = pop_first_nonempty_queue(project, profile=profile)

        if datum is None:
            return None
        else:
            AssignedData.objects.create(data=datum, profile=profile,
                                        queue=queue)
            return datum


def label_data(label, datum, profile):
    '''
    Record that a given datum has been labeled; remove its assignment, if any.
    '''
    current_training_set = datum.project.current_training_set

    with transaction.atomic():
        DataLabel.objects.create(data=datum,
                                label=label,
                                profile=profile,
                                training_set=current_training_set
                                )
        # There's a unique constraint on data/profile, so this is
        # guaranteed to return one object
        assignment = AssignedData.objects.filter(data=datum,
                                                profile=profile).get()
        queue = assignment.queue
        assignment.delete()
        DataQueue.objects.filter(data=datum, queue=queue).delete()


def get_assignments(profile, project, num_assignments):
    '''
    Check if a data is currently assigned to this profile/project;
    If so, return max(num_assignments, len(assigned) of it.
    If not, try to get a num_assigments of new assignments and return them.
    '''
    existing_assignments = AssignedData.objects.filter(
        profile=profile,
        queue__project=project)

    if len(existing_assignments) > 0:
        return [assignment.data for assignment in existing_assignments[:num_assignments]]
    else:
        data = []
        for i in range(num_assignments):
            assigned_datum = assign_datum(profile, project)
            if assigned_datum is None:
                break
            data.append(assigned_datum)
        return data


def unassign_datum(datum, profile):
    '''
    Remove a profile's assignment to a datum.  Re-add the datum to its
    respective queue in Redis.
    '''
    assignment = AssignedData.objects.filter(
        profile=profile,
        data=datum).get()

    queue = assignment.queue
    assignment.delete()

    settings.REDIS.lpush('queue:'+str(queue.pk), 'data:'+str(datum.pk))


def create_tfidf_matrix(data, max_df=0.95, min_df=0.05):
    """Create a TF-IDF matrix

    Args:
        data: List/Queryset of Data objects
    Returns:
        tf_idf_matrix: CSR-format tf-idf matrix
    """
    vectorizer = TfidfVectorizer(max_df=max_df, min_df=min_df)
    tf_idf_matrix = vectorizer.fit_transform([d.text for d in data])

    return tf_idf_matrix


def save_tfidf_matrix(matrix, project, prefix_dir=None):
    """Save tf-idf matrix to persistent volume storage as /data/tf_idf/<pk>.npz

    Args:
        matrix: CSR-format tf-idf matrix
        project: The project the data comes from
        prefix_dir: Prefix to add to file path, needed for testing
    Returns:
        file: The filepath to the saved matrix
    """
    file = '/data/tf_idf/' + str(project.pk) + '.npz'
    if prefix_dir is not None:
        file = os.path.join(prefix_dir, file.lstrip(os.path.sep))

    sparse.save_npz(file, matrix)

    return file


def load_tfidf_matrix(project, prefix_dir=None):
    """Load tf-idf matrix from persistent volume, otherwise None

    Args:
        project: Project object to retrieve tf-idf CSR from
        prefix_dir: Prefix to add to file path, needed for testing
    Returns:
        matrix or None
    """
    file = '/data/tf_idf/' + str(project.pk) + '.npz'
    if prefix_dir is not None:
        file = os.path.join(prefix_dir, file.lstrip(os.path.sep))

    if os.path.isfile(file):
        return sparse.load_npz(file)
    else:
        return None


def check_and_trigger_model(datum):
    """Given a recently assigned datum check if the project it belong to needs
       its model ran.  It the model needs to be run, start the model run and
       increment the project's current_training_set

    Args:
        datum: Recently assigne Data object
    """
    project = datum.project
    batch_size = project.labels.count() * 10
    labeled_data = DataLabel.objects.filter(data__project=project,
                                            training_set=project.current_training_set)

    if len(labeled_data) >= batch_size:
        project.update(F('current_training_set') + 1)
        model = train_and_save_model(project)
        predictions = predict_data(project, model)
        fill_queue(project.queue_set.get()) ### TODO: UPDATE FILL QUEUE FOR MODEL


def train_and_save_model(project, prefix_dir=None):
    """Given a project start training the model"""
    min_data_pk = project.data_set.all().order_by('pk')[0]
    labeled_data = DataLabel.objects.filter(data__project=project)
    labeled_indices_adjusted = [d.data.pk - min_data_pk for d in labeled_data]

    tf_idf = load_tfidf_matrix(project).A

    x, y = [], []
    for idx in labeled_indices_adjusted:
        x.append(tf_idf[idx,:])
        y.append(labaled_data.get(pk=idx+min_data_pk).label.pk)

    clf = LogisticRegression.fit(x, y)

    file = '/data/model_pickles/project:' + str(project.pk) + ':training:' \
         + str(project.current_training_set) + '.pkl'
    if prefix_dir is not None:
        file = os.path.join(prefix_dir, file.lstrip(os.path.sep))

    joblib.dump(clf, file)

    model = Model.objects.create(pickle_path=file, project=project)

    return model


def predict_data(project, model):
    """Given a project and its model, predict any unlabeled data"""
    min_data_pk = project.data_set.all().order_by('pk')[0]
    unlabeled_data = project.data_set.filter(data_label__isnull=True)
    unlabeled_indices_adjusted = [d.pk - min_data_pk for d in unlabeled_data]

    clf = joblib.load(model.pickle_path)
    load_tfidf_matrix(project).A

    x = []
    for idx in unlabeled_indices_adjusted:
        x.append(tf_idf[idx,:])

    predictions = clf.predict(x)

    bulk_predictions = []
    for datum, prediction in zip(unlabeled_data, predictions):
        bulk_predictions.append(DataPrediction(data=datum, model=model, label=prediction))
    prediction_objs = DataPrediction.bulk_create(bulk_predictions)

    return prediction_objs

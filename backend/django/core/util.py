import random
import redis
import math

from django.db import transaction, connection
from django.db.models import Count, Value, IntegerField, F
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import (Project, Data, Queue, DataQueue, User,
                         AssignedData, DataLabel)


# TODO: This create_queue should be refactored in favor of add_queue during issue
# #50 - Integrate Redis
def create_queue(project, label_form, permission_form):
    """
    Create a queue for a project.
    batch_size = 10*labels
    max_assigned = math.ceil(batch_size/#coders) [a]
    queue length = math.ceil(a)*c + math.ceil(a) * (c-1)

    labels and permissions are formset objects.
    """
    labels = [x.cleaned_data for x in label_form if x.cleaned_data != {}]
    permissions = [x.cleaned_data for x in permission_form if x.cleaned_data != {}]

    batch_size = 10 * len(labels)
    num_coders = len(permissions) + 1

    q_length = math.ceil(batch_size/num_coders) * num_coders + math.ceil(batch_size/num_coders) * (num_coders - 1)

    return Queue.objects.create(project=project, length=q_length)


# TODO: Divide these functions into a public/private API when we determine
#  what functionality is needed by the frontend.  This file is a little
#  intimidating to sort through at the moment.

def create_user(username, password, email):
    '''
    Create a user with the given attributes.
    Create a user in Django's authentication model and
    link it to our own project user model.
    '''
    auth_user = get_user_model().objects.create(
        username=username,
        password=password,
        email=email)

    return User.objects.get(auth_user=auth_user)


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

    This assumes redis is empty; throw an error if it isn't, since we'll
    add duplicate data without knowing any better.
    '''
    for key in settings.REDIS.scan_iter():
        raise ValueError('Redis database is not empty; it must be empty to initialize the '
                         'redis queues.')

    # Use a pipeline to reduce back-and-forth with the server
    pipeline = settings.REDIS.pipeline(transaction=False)

    assigned_data_ids = set((d.data_id for d in AssignedData.objects.all()))

    for queue in Queue.objects.all():
        data_ids = [d.pk for d in queue.data.all() if d.pk not in assigned_data_ids]
        if len(data_ids) > 0:
            # We'll get an error if we try to lpush without any data
            pipeline.lpush(queue.pk, *data_ids)

    pipeline.execute()


def clear_redis_queues():
    '''
    Clear the queues currently present in redis.
    '''
    settings.REDIS.flushdb()


def sync_redis_queues():
    '''
    Set the redis environment up to have the same state as the database, regardless
    of its current state.
    '''
    clear_redis_queues()
    init_redis_queues()


def create_project(name):
    '''
    Create a project with the given name.
    '''
    return Project.objects.create(name=name)


def add_data(project, data):
    '''
    Add data to an existing project.  Data should be an array of strings.
    '''
    bulk_data = (Data(text=d, project=project) for d in data)
    Data.objects.bulk_create(bulk_data)


def add_queue(project, length, user=None):
    '''
    Add a queue of the given length to the given project.  If a user is provided,
    assign the queue to that user.

    Return the created queue.
    '''
    return Queue.objects.create(length=length, project=project, user=user)


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


def pop_first_nonempty_queue(project, user=None):
    '''
    Determine which queues are eligible to be popped (and in what order)
    and pass them into redis to have the first nonempty one popped.
    Return a (queue, data item) tuple if one was found; return a (None, None)
    tuple if not.
    '''
    if user is not None:
        # Use priority to ensure we set user queues above project queues
        # in the resulting list; break ties by pk
        user_queues = project.queue_set.filter(user=user)
    else:
        user_queues = Queue.objects.none()
    user_queues = user_queues.annotate(priority=Value(1, IntegerField()))

    project_queues = (project.queue_set.filter(user=None)
                      .annotate(priority=Value(2, IntegerField())))

    eligible_queue_ids = [queue.pk for queue in
                          (user_queues.union(project_queues)
                           .order_by('priority', 'pk'))]

    if len(eligible_queue_ids) == 0:
        return (None, None)

    # Use a custom Lua script here to find the first nonempty queue atomically
    # and pop its first item.  If all queues are empty, return nil.
    script = settings.REDIS.register_script('''
    for _, k in pairs(KEYS) do
      local m = redis.call('LPOP', k)
      if m then
        return {tonumber(k), tonumber(m)}
      end
    end
    return nil
    ''')

    result = script(keys=eligible_queue_ids)

    if result is None:
        return (None, None)
    else:
        queue_id, data_id = result
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
    data_id = settings.REDIS.rpop(queue.pk)

    if data_id is None:
        return None

    data_obj = Data.objects.filter(pk=data_id).get()

    return data_obj


def get_nonempty_queue(project, user=None):
    '''
    Return the first nonempty queue for the given project and
    (optionally) user.

    Client code should prefer pop_first_nonempty_queue() if the
    intent is to pop the first nonempty queue, as it avoids
    concurrency issues.
    '''
    first_nonempty_queue = None

    # Only check for user queues if we were passed a user
    if user is not None:
        nonempty_user_queues = (project.queue_set
                                .filter(user=user)
                                .annotate(
                                    data_count=Count('data'))
                                .filter(data_count__gt=0))

        if len(nonempty_user_queues) > 0:
            first_nonempty_queue = nonempty_user_queues.first()

    # If we didn't find a user queue, check project queues
    if first_nonempty_queue is None:
        nonempty_queues = (project.queue_set
                           .filter(user=None)
                           .annotate(
                               data_count=Count('data'))
                           .filter(data_count__gt=0))

        if len(nonempty_queues) > 0:
            first_nonempty_queue = nonempty_queues.first()

    return first_nonempty_queue


def assign_datum(user, project):
    '''
    Given a user and project, figure out which queue to pull from;
    then pop a datum off that queue and assign it to the user.
    '''
    with transaction.atomic():
        queue, datum = pop_first_nonempty_queue(project, user=user)

        if datum is None:
            return None
        else:
            AssignedData.objects.create(data=datum, user=user,
                                        queue=queue)
            return datum


def label_data(label, datum, user):
    '''
    Record that a given datum has been labeled; remove its assignment, if any.
    '''
    with transaction.atomic():
        DataLabel.objects.create(data=datum,
                                label=label,
                                user=user)
        # There's a unique constraint on data/user, so this is
        # guaranteed to return one object
        assignment = AssignedData.objects.filter(data=datum,
                                                user=user).get()
        queue = assignment.queue
        assignment.delete()
        DataQueue.objects.filter(data=datum, queue=queue).delete()


def get_assignment(user, project):
    '''
    Check if a datum is currently assigned to this user/project;
    if so, return it.  If not, try to get a new assignment and return it.
    '''
    existing_assignments = AssignedData.objects.filter(
        user=user,
        queue__project=project)

    if len(existing_assignments) > 0:
        return existing_assignments.first().data
    else:
        return assign_datum(user, project)


def unassign_datum(datum, user):
    '''
    Remove a user's assignment to a datum.  Re-add the datum to its
    respective queue in Redis.
    '''
    assignment = AssignedData.objects.filter(
        user=user,
        data=datum).get()

    queue = assignment.queue
    assignment.delete()

    settings.REDIS.lpush(queue.pk, datum.pk)

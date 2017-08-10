import random
import redis

from django.conf import settings
from core.models import (Project, Data, Queue, DataQueue)

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
    '''
    conn = redis.StrictRedis.from_url(settings.REDIS_URL)
    # Use a pipeline to reduce back-and-forth with the server
    pipeline = conn.pipeline(transaction=False)

    for queue in Queue.objects.all():
        data_ids = [d.pk for d in queue.data.all()]
        if len(data_ids) > 0:
            # We'll get an error if we try to lpush without any data
            pipeline.lpush(queue.pk, *data_ids)

    pipeline.execute()


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
    current_queue_len = queue.data.count()

    data_filters = {
        'project': queue.project,
        'labelers': None,
        'queues': None
    }

    try:
        # TODO: This has concurrency issues -- if multiple queues are filled
        # at the same time, they'll both draw their sample from the same set
        # of data and may assign some of the same data objects.
        # Need to have the sampling and insert in the same query,
        # (INSERT INTO ... SELECT ...)
        # which apparently requires raw SQL.  May require SELECT FOR UPDATE
        # SKIP LOCKED (Postgres 9.5+).
        queue_data = iter_sample(Data.objects
                                 .filter(**data_filters)
                                 .iterator(), queue.length - current_queue_len)
    except ValueError:
        # There isn't enough data left to fill the queue, so assign all of it
        queue_data = Data.objects.filter(**data_filters)

    DataQueue.objects.bulk_create(
        (DataQueue(queue=queue, data=d) for d in queue_data))

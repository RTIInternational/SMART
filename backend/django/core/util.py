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

def create_project(project_attrs, data):
    '''
    Create a project with the given attributes and data,
    initializing a project queue and returning the created
    project.

    Data should be an array of strings.
    '''
    project = Project.objects.create(**project_attrs)

    bulk_data = (Data(text=d, project=project) for d in data)
    Data.objects.bulk_create(bulk_data)

    return project

def add_queue(project, length, user=None):
    '''
    Add a queue of the given length to the given project.  If a user is provided,
    assign the queue to that user.

    Return the created queue.
    '''
    return Queue.objects.create(length=length, project=project, user=user)

def fill_queue(queue):
    '''
    Fill a queue with unlabeled data randomly selected from the queue's project.
    The queue doesn't need to be empty.

    If there isn't enough unlabeled data left to fill the queue, use all the
    unlabeled data available.
    '''
    current_queue_len = queue.data.count()

    try:
        queue_data = iter_sample(Data.objects
                                 .filter(project=queue.project,
                                         labelers=None)
                                 .iterator(), queue.length - current_queue_len)
    except ValueError:
        # There isn't enough data left to fill the queue, so assign all of it
        queue_data = Data.objects.filter(project=queue.project)

    DataQueue.objects.bulk_create(
        (DataQueue(queue=queue, data=d) for d in queue_data))

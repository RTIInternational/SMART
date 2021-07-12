from django.conf import settings
from django.db.models import Max, Min
from django.db.utils import ProgrammingError

from core.models import AssignedData, Data, Queue


def redis_serialize_queue(queue):
    """Serialize a queue object for redis queues.

    The format is 'queue:<pk>'
    """
    return "queue:" + str(queue.pk)


def redis_serialize_set(queue):
    """Serialize a queue object for redis sets.

    The format is 'set:<pk>'
    """
    return "set:" + str(queue.pk)


def redis_serialize_data(datum):
    """Serialize a data object for redis.

    The format is 'data:<pk>'
    """
    return "data:" + str(datum.pk)


def redis_parse_queue(queue_key):
    """Parse a queue key from redis and return the Queue object."""
    queue_pk = queue_key.decode().split(":")[1]
    return Queue.objects.get(pk=queue_pk)


def redis_parse_data(datum_key):
    """Parse a datum key from redis and return the Data object."""
    datum_pk = datum_key.decode().split(":")[1]
    return Data.objects.get(pk=datum_pk)


def redis_parse_list_dataids(data_ids):
    """Parse a list of redis data ids and return a list of primary key strings."""
    return [d.decode().split(":")[1] for d in data_ids]


def get_ordered_data(data_ids, orderby):
    """Order a list of data ids by the orderby option.

        least confident returns in descending order
        margin sampling returns in ascending order
        entropy returns in descending order
        random returns in random order (different each time function called)

    Args:
        data_ids: List of data_ids
        orderby: String of order by options. ["random", "least confident",
            "margin sampling", "entropy"]
    Returns:
        Query set of ordered data objects
    """
    ORDERBY_OPTIONS = ["random", "least confident", "margin sampling", "entropy"]
    if orderby not in ORDERBY_OPTIONS:
        raise ValueError(
            "orderby parameter must be one of the following: "
            + " ".join(ORDERBY_OPTIONS)
        )

    data_objs = Data.objects.filter(pk__in=data_ids)

    if orderby == "random":
        return data_objs.order_by("?")
    elif orderby == "least confident":
        return data_objs.annotate(
            max_least_confident=Max("datauncertainty__least_confident")
        ).order_by("-max_least_confident")
    elif orderby == "margin sampling":
        return data_objs.annotate(
            min_margin_sampling=Min("datauncertainty__margin_sampling")
        ).order_by("min_margin_sampling")
    elif orderby == "entropy":
        return data_objs.annotate(max_entropy=Max("datauncertainty__entropy")).order_by(
            "-max_entropy"
        )


def init_redis():
    """Create a redis queue and set for each queue in the database and fill it with the
    data linked to the queue.

    This will remove any existing queue keys from redis and re-populate the redis db to
    be in sync with the postgres state
    """
    # Use a pipeline to reduce back-and-forth with the server
    try:
        assigned_data_ids = set((d.data_id for d in AssignedData.objects.all()))
    except ProgrammingError:
        raise ValueError(
            "There are unrun migrations.  Please migrate the database."
            " Use `docker-compose run --rm smart_backend ./migrate.sh`"
            " Then restart the django server."
        )

    pipeline = settings.REDIS.pipeline(transaction=False)

    existing_queue_keys = [key for key in settings.REDIS.scan_iter("queue:*")]
    existing_set_keys = [key for key in settings.REDIS.scan_iter("set:*")]
    if len(existing_queue_keys) > 0:
        # We'll get an error if we try to del without any keys
        pipeline.delete(*existing_queue_keys)
    if len(existing_set_keys) > 0:
        pipeline.delete(*existing_set_keys)

    pipeline.execute()

    for queue in Queue.objects.all():
        data_ids = [d.pk for d in queue.data.all() if d.pk not in assigned_data_ids]
        data_ids = [
            redis_serialize_data(d)
            for d in get_ordered_data(data_ids, "least confident")
        ]
        if len(data_ids) > 0:
            # We'll get an error if we try to lpush without any data
            pipeline.sadd(redis_serialize_set(queue), *data_ids)
            pipeline.lpush(redis_serialize_queue(queue), *data_ids)

    pipeline.execute()


def sync_redis_objects(queue, orderby):
    """Given a DataQueue sync the redis set with the DataQueue and then update the redis
    queue with the appropriate new ordered data."""
    ORDERBY_OPTIONS = ["random", "least confident", "margin sampling", "entropy"]
    if orderby not in ORDERBY_OPTIONS:
        raise ValueError(
            "orderby parameter must be one of the following: "
            + " ".join(ORDERBY_OPTIONS)
        )

    data_ids = [redis_serialize_data(d) for d in queue.data.all()]
    if len(data_ids) > 0:
        settings.REDIS.sadd(redis_serialize_set(queue), *data_ids)

        redis_set_data = settings.REDIS.smembers(redis_serialize_set(queue))
        redis_queue_data = settings.REDIS.lrange(redis_serialize_queue(queue), 0, -1)

        # IDs not already in redis queue
        new_data_ids = redis_parse_list_dataids(
            redis_set_data.difference(set(redis_queue_data))
        )

        # IDs not already assigned
        new_data_ids = set(new_data_ids).difference(
            [str(a.data.pk) for a in AssignedData.objects.filter(queue=queue)]
        )

        ordered_data_ids = [
            redis_serialize_data(d) for d in get_ordered_data(new_data_ids, orderby)
        ]

        if len(ordered_data_ids) > 0:
            settings.REDIS.rpush(redis_serialize_queue(queue), *ordered_data_ids)

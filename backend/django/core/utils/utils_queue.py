import math

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Count, F, IntegerField, Value

from core.models import (
    AssignedData,
    Data,
    DataLabel,
    DataQueue,
    DataUncertainty,
    IRRLog,
    Model,
    Queue,
    RecycleBin,
)
from core.utils.utils_redis import (
    redis_parse_data,
    redis_parse_queue,
    redis_serialize_queue,
    sync_redis_objects,
)


def find_queue_length(batch_size, num_coders):
    """Determine the length of the queue given by the batch_size and number of coders.

    Args:
        batch_size [default: number of labels * 10]
        num_coders [creator, admins, coders]
    Returns:
        queue_length
    """
    return math.ceil(batch_size / num_coders) * num_coders + math.ceil(
        batch_size / num_coders
    ) * (num_coders - 1)


def add_queue(project, length, type="normal", profile=None):
    """Add a queue of the given length to the given project.  If a profile is provided,
    assign the queue to that profile.

    Return the created queue.
    """
    return Queue.objects.create(
        length=length, project=project, profile=profile, type=type
    )


def fill_queue(queue, orderby, irr_queue=None, irr_percent=10, batch_size=30):
    """Fill a queue with unlabeled, unassigned data randomly selected from the queue's
    project. The queue doesn't need to be empty.

    If there isn't enough data left to fill the queue, use all the
    data available.

    Takes an orderby arguement to fill the qeuue based on uncertainty sampling if
    the project has a trained model

    Fill the IRR queue with the given percentage of values
    """

    ORDERBY_VALUE = {
        "random": "random()",
        "least confident": "uncertainty.least_confident DESC",
        "margin sampling": "uncertainty.margin_sampling ASC",
        "entropy": "uncertainty.entropy DESC",
    }
    if orderby not in ORDERBY_VALUE.keys():
        raise ValueError(
            "orderby parameter must be one of the following: " + " ".join(ORDERBY_VALUE)
        )

    recycled_data = RecycleBin.objects.filter(data__project=queue.project).values_list(
        "data__pk", flat=True
    )
    data_filters = {
        "project": queue.project,
        "labelers": None,
        "queues": None,
        "irr_ind": False,
    }

    eligible_data = Data.objects.filter(**data_filters).exclude(pk__in=recycled_data)

    cte_sql, cte_params = eligible_data.query.sql_with_params()

    # get the join clause that controls how the data is selected
    join_clause = get_join_clause(orderby, queue)

    # First process the IRR data
    if irr_queue:
        # if the irr queue is given, want to fill it with a given percent of
        # the batch size
        num_irr = math.ceil(batch_size * (irr_percent / 100))
        num_elements = len(DataQueue.objects.filter(queue=irr_queue))
        queue_size = irr_queue.length

        # get the number of elements to add to the irr queue
        irr_sample_size_sql, irr_sample_size_params = get_queue_size_params(
            irr_queue, queue_size, num_elements, num_irr, irr_queue
        )
        # get the sql for adding the elements
        irr_sql = generate_sql_for_fill_queue(
            irr_queue, ORDERBY_VALUE[orderby], join_clause, cte_sql, irr_sample_size_sql
        )

        with connection.cursor() as c:
            c.execute(irr_sql, (*cte_params, *irr_sample_size_params))

        data_ids = []
        with transaction.atomic():
            irr_data = DataQueue.objects.filter(queue=irr_queue.pk)
            for d in irr_data:
                data_ids.append(d.data.pk)
            Data.objects.filter(pk__in=data_ids).update(irr_ind=True)

        sync_redis_objects(irr_queue, orderby)

        # get new eligible data by filtering out what was just chosen
        eligible_data = eligible_data.exclude(pk__in=data_ids)
        cte_sql, cte_params = eligible_data.query.sql_with_params()

    # get the remaining space in the normal queue
    non_irr_batch_size = math.ceil(batch_size * ((100 - irr_percent) / 100))
    num_in_queue = len(DataQueue.objects.filter(queue=queue))
    queue_size = queue.length
    # if there is not much space or we are not filling the irr queue, just
    # fill the normal queue to the top
    sample_size_sql, sample_size_params = get_queue_size_params(
        queue, queue_size, num_in_queue, non_irr_batch_size, irr_queue
    )

    sql = generate_sql_for_fill_queue(
        queue, ORDERBY_VALUE[orderby], join_clause, cte_sql, sample_size_sql
    )

    with connection.cursor() as c:
        c.execute(sql, (*cte_params, *sample_size_params))

    sync_redis_objects(queue, orderby)


def generate_sql_for_fill_queue(queue, orderby_value, join_clause, cte_sql, size_sql):
    """This function merely takes the given paramters and returns an sql query to
    execute for filling the queue."""
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
    {join_clause}
    ORDER BY
        {orderby_value}
    LIMIT ({sample_size_sql});
    """.format(
        cte_sql=cte_sql,
        dataqueue_table=DataQueue._meta.db_table,
        dataqueue_data_id_col=DataQueue._meta.get_field("data").column,
        dataqueue_queue_id_col=DataQueue._meta.get_field("queue").column,
        data_pk_col=Data._meta.pk.name,
        queue_id=queue.pk,
        join_clause=join_clause,
        orderby_value=orderby_value,
        sample_size_sql=size_sql,
    )
    return sql


def get_join_clause(orderby, queue):
    """This function generates the join clause used to fill queues."""
    if orderby == "random":
        join_clause = ""
    else:
        join_clause = """
        LEFT JOIN
            {datauncertainty_table} AS uncertainty
          ON
            eligible_data.{data_pk_col} = uncertainty.{datauncertainty_data_id_col}
        WHERE
            uncertainty.{datauncertainty_model_id_col} = (
                SELECT max(c_model.{model_pk_col})
                FROM {model_table} AS c_model
                WHERE c_model.{model_project_id_col} = {project_id}
            )
        """.format(
            datauncertainty_table=DataUncertainty._meta.db_table,
            data_pk_col=Data._meta.pk.name,
            datauncertainty_data_id_col=DataUncertainty._meta.get_field("data").column,
            datauncertainty_model_id_col=DataUncertainty._meta.get_field(
                "model"
            ).column,
            model_pk_col=Model._meta.pk.name,
            model_table=Model._meta.db_table,
            model_project_id_col=Model._meta.get_field("project").column,
            project_id=queue.project.pk,
        )
    return join_clause


def get_queue_size_params(queue, queue_size, num_in_queue, batch_size, irr_queue):
    """Get the sql parameters for the number of items to add to the queue."""
    # if there is less space in the queue than the default number of
    # elements to add, or we are trying to fill the queue to the top
    # (irr_queue=None in the second case)
    if (queue_size - num_in_queue < batch_size) or not (irr_queue):
        sample_size_sql, sample_size_params = (
            Queue.objects.filter(pk=queue.pk)
            .annotate(sample_size=F("length") - Count("data"))
            .values("sample_size")
            .query.sql_with_params()
        )
    else:
        # just add the number requested (some percent of the batch size)
        sample_size_sql, sample_size_params = (
            Queue.objects.filter(pk=queue.pk)
            .annotate(sample_size=Value(batch_size, IntegerField()))
            .values("sample_size")
            .query.sql_with_params()
        )
    return sample_size_sql, sample_size_params


def pop_first_nonempty_queue(project, profile=None, type="normal"):
    """Determine which queues are eligible to be popped (and in what order) and pass
    them into redis to have the first nonempty one popped.

    Return a (queue, data item) tuple if one was found; return a (None, None) tuple if
    not.
    """
    if profile is not None:
        # Use priority to ensure we set profile queues above project queues
        # in the resulting list; break ties by pk
        profile_queues = project.queue_set.filter(profile=profile, type=type)
    else:
        profile_queues = Queue.objects.none()
    profile_queues = profile_queues.annotate(priority=Value(1, IntegerField()))

    project_queues = project.queue_set.filter(profile=None, type=type).annotate(
        priority=Value(2, IntegerField())
    )

    eligible_queue_ids = [
        redis_serialize_queue(queue)
        for queue in (profile_queues.union(project_queues).order_by("priority", "pk"))
    ]

    if type == "irr":
        for queue_id in eligible_queue_ids:
            queue = redis_parse_queue(queue_id.encode())

            # first get the assigned data that was already labeled, or data already assigned
            labeled_irr_data = DataLabel.objects.filter(profile=profile).values_list(
                "data", flat=True
            )
            assigned_data = AssignedData.objects.filter(
                profile=profile, queue=queue
            ).values_list("data", flat=True)
            skipped_data = IRRLog.objects.filter(
                profile=profile, label__isnull=True
            ).values_list("data", flat=True)
            assigned_unlabeled = (
                DataQueue.objects.filter(queue=queue)
                .exclude(data__in=labeled_irr_data)
                .exclude(data__in=assigned_data)
                .exclude(data__in=skipped_data)
            )

            # if there are no elements, return none
            if len(assigned_unlabeled) == 0:
                return (None, None)
            else:
                # else, get the first element off the group and return it
                datum = Data.objects.get(pk=assigned_unlabeled[0].data.pk)
                return (queue, datum)
    if len(eligible_queue_ids) == 0:
        return (None, None)

    # Use a custom Lua script here to find the first nonempty queue atomically
    # and pop its first item.  If all queues are empty, return nil.
    script = settings.REDIS.register_script(
        """
    for _, k in pairs(KEYS) do
      local m = redis.call('LPOP', k)
      if m then
        return {k, m}
      end
    end
    return nil
    """
    )

    result = script(keys=eligible_queue_ids)

    if result is None:
        return (None, None)
    else:
        queue_key, data_key = result
        return (redis_parse_queue(queue_key), redis_parse_data(data_key))


def pop_queue(queue):
    """Remove a datum from the given queue (in redis and the database) and return it.

    Returns None and does nothing if the queue is empty.

    Client code should prefer pop_first_nonempty_queue() if the
    intent is to pop the first nonempty queue, as it avoids
    concurrency issues.
    """
    # Redis first, since this op is guaranteed to be atomic
    data_id = settings.REDIS.rpop(redis_serialize_queue(queue))

    if data_id is None:
        return None
    else:
        data_id = data_id.decode().split(":")[1]

    data_obj = Data.objects.filter(pk=data_id).get()

    return data_obj


def get_nonempty_queue(project, profile=None):
    """Return the first nonempty queue for the given project and (optionally) profile.

    Client code should prefer pop_first_nonempty_queue() if the intent is to pop the
    first nonempty queue, as it avoids concurrency issues.
    """
    first_nonempty_queue = None

    # Only check for profile queues if we were passed a profile
    if profile is not None:
        nonempty_profile_queues = (
            project.queue_set.filter(profile=profile, type="normal")
            .annotate(data_count=Count("data"))
            .filter(data_count__gt=0)
        )

        if len(nonempty_profile_queues) > 0:
            first_nonempty_queue = nonempty_profile_queues.first()

    # If we didn't find a profile queue, check project queues
    if first_nonempty_queue is None:
        nonempty_queues = (
            project.queue_set.filter(profile=None, type="normal")
            .annotate(data_count=Count("data"))
            .filter(data_count__gt=0)
        )

        if len(nonempty_queues) > 0:
            first_nonempty_queue = nonempty_queues.first()

    return first_nonempty_queue


def handle_empty_queue(profile, project):
    """Given a profile and project, check if there is any data left for the user to
    code, if not then refill the queue.

    Args:
        profile: user profile object
        project: project object
    """
    queue = Queue.objects.get(project=project, type="normal")
    irr_queue = Queue.objects.get(project=project, type="irr")

    queue_count = DataQueue.objects.filter(queue=queue).count()
    irr_count = DataQueue.objects.filter(queue=irr_queue).count()
    assigned_toOthers_count = (
        AssignedData.objects.filter(queue=queue).exclude(profile=profile).count()
    )
    irr_labeled_count = (
        IRRLog.objects.filter(profile=profile, data__project=project).count()
        + DataLabel.objects.filter(
            profile=profile, data__dataqueue__queue=irr_queue
        ).count()
    )

    if queue_count - assigned_toOthers_count == 0 and irr_count == irr_labeled_count:
        # if there is a model, use the orderby of the project, otherwise random
        if len(Model.objects.filter(project=project)) > 0:
            fill_queue(
                queue=queue,
                orderby=project.learning_method,
                irr_queue=irr_queue,
                irr_percent=project.percentage_irr,
                batch_size=project.batch_size,
            )
        else:
            fill_queue(
                queue=queue,
                orderby="random",
                irr_queue=irr_queue,
                irr_percent=project.percentage_irr,
                batch_size=project.batch_size,
            )

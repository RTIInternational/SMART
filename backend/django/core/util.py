import random
import redis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.externals import joblib
from scipy import sparse
import os
import math
import numpy as np
import hashlib
import pandas as pd
from django.utils import timezone
# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
# Disable warning for false positive warning that should only trigger on chained assignment
pd.options.mode.chained_assignment = None  # default='warn'
from celery.result import AsyncResult

from django.db import transaction, connection
from django.db.models import Count, Value, IntegerField, F, Max, Min
from django.db.utils import ProgrammingError
from django.contrib.auth import get_user_model
from django.conf import settings

from core.models import (Project, Data, Queue, DataQueue, Profile, Label,
                         AssignedData, DataLabel, Model, DataPrediction,
                         DataUncertainty, TrainingSet, IRRLog)
from core import tasks


# TODO: Divide these functions into a public/private API when we determine
#  what functionality is needed by the frontend.  This file is a little
#  intimidating to sort through at the moment.


def redis_serialize_queue(queue):
    """Serialize a queue object for redis queues.  The format is 'queue:<pk>'"""
    return 'queue:' + str(queue.pk)


def redis_serialize_set(queue):
    """Serialize a queue object for redis sets.  The format is 'set:<pk>'"""
    return 'set:' + str(queue.pk)


def redis_serialize_data(datum):
    """Serialize a data object for redis.  The format is 'data:<pk>'"""
    return 'data:' + str(datum.pk)


def redis_parse_queue(queue_key):
    """Parse a queue key from redis and return the Queue object"""
    queue_pk = queue_key.decode().split(':')[1]
    return Queue.objects.get(pk=queue_pk)


def redis_parse_data(datum_key):
    """Parse a datum key from redis and return the Data object"""
    datum_pk = datum_key.decode().split(':')[1]
    return Data.objects.get(pk=datum_pk)


def redis_parse_list_dataids(data_ids):
    """Parse a list of redis data ids and return a list of primary key strings"""
    return [d.decode().split(':')[1] for d in data_ids]


def md5_hash(obj):
    """Return MD5 hash hexdigest of obj; returns None if obj is None"""
    if obj is not None:
        return hashlib.md5(obj.encode('utf-8', errors='ignore')).hexdigest()
    else:
        return None


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


def init_redis():
    '''
    Create a redis queue and set for each queue in the database and fill it with
    the data linked to the queue.

    This will remove any existing queue keys from redis and re-populate the redis
    db to be in sync with the postgres state
    '''
    # Use a pipeline to reduce back-and-forth with the server
    try:
        assigned_data_ids = set((d.data_id for d in AssignedData.objects.all()))
    except ProgrammingError:
        raise ValueError('There are unrun migrations.  Please migrate the database.'\
                         ' Use `docker-compose run --rm smart_backend ./migrate.sh`'\
                         ' Then restart the django server.')

    pipeline = settings.REDIS.pipeline(transaction=False)

    existing_queue_keys = [key for key in settings.REDIS.scan_iter('queue:*')]
    existing_set_keys = [key for key in settings.REDIS.scan_iter('set:*')]
    if len(existing_queue_keys) > 0:
        # We'll get an error if we try to del without any keys
        pipeline.delete(*existing_queue_keys)
    if len(existing_set_keys) > 0:
        pipeline.delete(*existing_set_keys)

    pipeline.execute()

    for queue in Queue.objects.all():
        data_ids = [d.pk for d in queue.data.all() if d.pk not in assigned_data_ids]
        data_ids = [redis_serialize_data(d) for d in get_ordered_data(data_ids, 'least confident')]
        if len(data_ids) > 0:
            # We'll get an error if we try to lpush without any data
            pipeline.sadd(redis_serialize_set(queue), *data_ids)
            pipeline.lpush(redis_serialize_queue(queue), *data_ids)

    pipeline.execute()


def sync_redis_objects(queue, orderby):
    """Given a DataQueue sync the redis set with the DataQueue and then update
        the redis queue with the appropriate new ordered data.
    """
    ORDERBY_OPTIONS = ['random', 'least confident', 'margin sampling', 'entropy']
    if orderby not in ORDERBY_OPTIONS:
        raise ValueError('orderby parameter must be one of the following: ' +
                         ' '.join(ORDERBY_OPTIONS))

    data_ids = [redis_serialize_data(d) for d in queue.data.all()]
    if len(data_ids) > 0:
        settings.REDIS.sadd(redis_serialize_set(queue), *data_ids)

        redis_set_data = settings.REDIS.smembers(redis_serialize_set(queue))
        redis_queue_data = settings.REDIS.lrange(redis_serialize_queue(queue), 0, -1)

        # IDs not already in redis queue
        new_data_ids = redis_parse_list_dataids(redis_set_data.difference(set(redis_queue_data)))

        # IDs not already assigned
        new_data_ids = set(new_data_ids).difference([str(a.data.pk) for a in AssignedData.objects.filter(queue=queue)])

        ordered_data_ids = [redis_serialize_data(d) for d in get_ordered_data(new_data_ids, orderby)]

        if len(ordered_data_ids) > 0:
            settings.REDIS.rpush(redis_serialize_queue(queue), *ordered_data_ids)


def create_project(name, creator):
    '''
    Create a project with the given name and creator.
    '''
    proj = Project.objects.create(name=name, creator=creator)
    training_set = TrainingSet.objects.create(project=proj, set_number=0)

    return proj


def add_data(project, df):
    '''
    Add data to an existing project.  df should be two column dataframe with
    columns Text and Label.  Label can be empty and should have at least one
    null value.  Any row that has Label should be added to DataLabel
    '''
    # Create hash of text and drop duplicates
    df['hash'] = df['Text'].apply(md5_hash)
    df.drop_duplicates(subset='hash', keep='first', inplace=True)

    # Limit the number of rows to 2mil
    df = df[:2000000]

    # Set the index column.  If previous data exists then we want to start the
    # index from the end of the current data.  The next new index should start
    # at the count of existing data since the existing df_idx is zero indexed
    num_existing_data = Data.objects.filter(project=project).count()
    df.reset_index(drop=True, inplace=True)
    df['idx'] = df.index + num_existing_data

    # Create the data objects
    df['object'] = df.apply(lambda x: Data(text=x['Text'], project=project,
                                            hash=x['hash'], df_idx=x['idx']), axis=1)
    data = Data.objects.bulk_create(df['object'].tolist())

    labels = {}
    for l in project.labels.all():
        labels[l.name] = l

    # Find the data that has labels
    labeled_df = df[~pd.isnull(df['Label'])]
    if len(labeled_df) > 0:
        labels = DataLabel.objects.bulk_create(
            [DataLabel(data=row['object'],
                       profile=project.creator,
                       label=labels[row['Label']],
                       training_set=project.get_current_training_set())
             for i, row in labeled_df.iterrows()]
        )

    return data


def find_queue_length(batch_size, num_coders):
    """Determine the length of the queue given by the batch_size and number of coders

    Args:
        batch_size [number of labels * 10]
        num_coders [creator, admins, coders]
    Returns:
        queue_length
    """
    return math.ceil(batch_size/num_coders) * num_coders + math.ceil(batch_size/num_coders) * (num_coders - 1)


def add_queue(project, length, admin = False, irr = False, profile=None):
    '''
    Add a queue of the given length to the given project.  If a profile is provided,
    assign the queue to that profile.

    Return the created queue.
    '''
    return Queue.objects.create(length=length, project=project, profile=profile, admin = admin, irr=irr)


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
    ORDERBY_OPTIONS = ['random', 'least confident', 'margin sampling', 'entropy']
    if orderby not in ORDERBY_OPTIONS:
        raise ValueError('orderby parameter must be one of the following: ' +
                         ' '.join(ORDERBY_OPTIONS))

    data_objs = Data.objects.filter(pk__in=data_ids)

    if orderby == 'random':
        return data_objs.order_by('?')
    elif orderby == 'least confident':
        return data_objs.annotate(max_least_confident=Max('datauncertainty__least_confident')).order_by('-max_least_confident')
    elif orderby == 'margin sampling':
        return data_objs.annotate(min_margin_sampling=Min('datauncertainty__margin_sampling')).order_by('min_margin_sampling')
    elif orderby == 'entropy':
        return data_objs.annotate(max_entropy=Max('datauncertainty__entropy')).order_by('-max_entropy')


def fill_queue(queue, orderby,  irr_queue = None, irr_percent = 10, batch_size = 30 ):
    '''
    Fill a queue with unlabeled, unassigned data randomly selected from
    the queue's project. The queue doesn't need to be empty.

    If there isn't enough data left to fill the queue, use all the
    data available.

    Takes an orderby arguement to fill the qeuue based on uncertainty sampling if
    the project has a trained model

    Fill the IRR queue with the given percentage of values
    '''
    ORDERBY_VALUE = {
        'random': 'random()',
        'least confident': 'uncertainty.least_confident DESC',
        'margin sampling': 'uncertainty.margin_sampling ASC',
        'entropy': 'uncertainty.entropy DESC',
    }
    if orderby not in ORDERBY_VALUE.keys():
        raise ValueError('orderby parameter must be one of the following: ' +
                         ' '.join(ORDERBY_VALUE))

    data_filters = {
        'project': queue.project,
        'labelers': None,
        'queues': None
    }

    eligible_data = Data.objects.filter(**data_filters)
    cte_sql, cte_params = eligible_data.query.sql_with_params()


    if orderby == 'random':
        join_clause = ''
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
            datauncertainty_data_id_col=DataUncertainty._meta.get_field('data').column,
            datauncertainty_model_id_col=DataUncertainty._meta.get_field('model').column,
            model_pk_col=Model._meta.pk.name,
            model_table=Model._meta.db_table,
            model_project_id_col=Model._meta.get_field('project').column,
            project_id=queue.project.pk)


    #First get the IRR data, then remove it from eligible data to avoid overlap
    if irr_queue:
        #if the irr queue is given, want to fill it with a given percent of
        #the batch size
        num_irr = math.ceil(batch_size * (irr_percent/100))
        num_elements = len(DataQueue.objects.filter(queue=irr_queue))

        queue_size = irr_queue.length
        if queue_size - num_elements < num_irr:
            irr_sample_size_sql, irr_sample_size_params = (Queue.objects.filter(pk=irr_queue.pk)
                                                .annotate(sample_size=F('length') - Count('data'))
                                                .values('sample_size')
                                                .query.sql_with_params())
        else:
            irr_sample_size_sql, irr_sample_size_params = (Queue.objects.filter(pk=irr_queue.pk)
                                                .annotate(sample_size=Value(num_irr, IntegerField()))
                                                .values('sample_size')
                                                .query.sql_with_params())
        irr_sql = """
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
            dataqueue_data_id_col=DataQueue._meta.get_field('data').column,
            dataqueue_queue_id_col=DataQueue._meta.get_field('queue').column,
            data_pk_col=Data._meta.pk.name,
            queue_id=irr_queue.pk,
            join_clause=join_clause,
            orderby_value=ORDERBY_VALUE[orderby],
            sample_size_sql=irr_sample_size_sql)

        with connection.cursor() as c:
            c.execute(irr_sql, (*cte_params, *irr_sample_size_params))

        with transaction.atomic():
            irr_data = DataQueue.objects.filter(queue=irr_queue.pk)
            data_ids = []
            for d in irr_data:
                data_ids.append(d.data.df_idx)
            Data.objects.filter(df_idx__in=data_ids).update(irr_ind=True)

        sync_redis_objects(irr_queue, orderby)

        #get new eligible data by filtering out what was just chosen
        data_filters = {
            'project': queue.project,
            'labelers': None,
            'queues': None,
            'irr_ind':False
        }
        eligible_data = Data.objects.filter(**data_filters)
        cte_sql, cte_params = eligible_data.query.sql_with_params()

    #get the remaining space in the normal queue
    sample_size_sql, sample_size_params = (Queue.objects.filter(pk=queue.pk)
                                            .annotate(sample_size=F('length') - Count('data'))
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
    {join_clause}
    ORDER BY
        {orderby_value}
    LIMIT ({sample_size_sql});
    """.format(
        cte_sql=cte_sql,
        dataqueue_table=DataQueue._meta.db_table,
        dataqueue_data_id_col=DataQueue._meta.get_field('data').column,
        dataqueue_queue_id_col=DataQueue._meta.get_field('queue').column,
        data_pk_col=Data._meta.pk.name,
        queue_id=queue.pk,
        join_clause=join_clause,
        orderby_value=ORDERBY_VALUE[orderby],
        sample_size_sql=sample_size_sql)

    with connection.cursor() as c:
        c.execute(sql, (*cte_params, *sample_size_params))

    sync_redis_objects(queue, orderby)


def pop_first_nonempty_queue(project, profile=None, admin=False, irr=False):
    '''
    Determine which queues are eligible to be popped (and in what order)
    and pass them into redis to have the first nonempty one popped.
    Return a (queue, data item) tuple if one was found; return a (None, None)
    tuple if not.
    '''
    if profile is not None:
        # Use priority to ensure we set profile queues above project queues
        # in the resulting list; break ties by pk
        profile_queues = project.queue_set.filter(profile=profile, admin=admin, irr=irr)
    else:
        profile_queues = Queue.objects.none()
    profile_queues = profile_queues.annotate(priority=Value(1, IntegerField()))

    project_queues = (project.queue_set.filter(profile=None, admin=admin, irr=irr)
                      .annotate(priority=Value(2, IntegerField())))

    eligible_queue_ids = [redis_serialize_queue(queue) for queue in
                          (profile_queues.union(project_queues)
                           .order_by('priority', 'pk'))]


    if irr:
        #######NEED TO SORT THE QUEUE SO THE LABELED STUFF IS AT THE BOTTOM#######
        for queue in eligible_queue_ids:
            queue_id = int(queue.replace("queue:",""))

            #first get the assigned data that was already labeled, or data already assigned
            labeled_irr_data = DataLabel.objects.filter(profile=profile).values_list('data',flat=True)
            assigned_data = AssignedData.objects.filter(profile=profile, queue=queue_id).values_list('data',flat=True)
            assigned_unlabeled = DataQueue.objects.filter(queue=queue_id).exclude(data__in=labeled_irr_data).exclude(data__in=assigned_data)

            #if there are no elements, return none
            if len(assigned_unlabeled) == 0:
                return (None, None)
            else:
                #else, get the first element off the group and return it
                datum = Data.objects.get(pk=assigned_unlabeled[0].data.pk)
                queue_obj = Queue.objects.get(pk=queue_id)
                return (queue_obj, datum)
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
        queue_key, data_key = result
        return (redis_parse_queue(queue_key),
                redis_parse_data(data_key))


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
    data_id = settings.REDIS.rpop(redis_serialize_queue(queue))

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
                                .filter(profile=profile, admin=False)
                                .annotate(
                                    data_count=Count('data'))
                                .filter(data_count__gt=0))

        if len(nonempty_profile_queues) > 0:
            first_nonempty_queue = nonempty_profile_queues.first()

    # If we didn't find a profile queue, check project queues
    if first_nonempty_queue is None:
        nonempty_queues = (project.queue_set
                           .filter(profile=None, admin=False)
                           .annotate(
                               data_count=Count('data'))
                           .filter(data_count__gt=0))

        if len(nonempty_queues) > 0:
            first_nonempty_queue = nonempty_queues.first()

    return first_nonempty_queue


def assign_datum(profile, project, irr=False):
    '''
    Given a profile and project, figure out which queue to pull from;
    then pop a datum off that queue and assign it to the profile.
    '''
    with transaction.atomic():
        queue, datum = pop_first_nonempty_queue(project, profile=profile, irr=irr)
        if datum is None:
            return None
        else:
            num_labeled = DataLabel.objects.filter(data=datum, profile=profile).count()
            if num_labeled == 0:
                AssignedData.objects.create(data=datum, profile=profile,
                                        queue=queue)
                return datum
            else:
                return None


def label_data(label, datum, profile, time):
    '''
    Record that a given datum has been labeled; remove its assignment, if any.

    Remove datum from DataQueue and its assocaited redis set.
    '''
    current_training_set = datum.project.get_current_training_set()

    irr_data = datum.irr_ind

    with transaction.atomic():
        DataLabel.objects.create(data=datum,
                                label=label,
                                profile=profile,
                                training_set=current_training_set,
                                time_to_label=time,
                                timestamp = timezone.now()
                                )
        # There's a unique constraint on data/profile, so this is
        # guaranteed to return one object
        assignment = AssignedData.objects.filter(data=datum,
                                                profile=profile).get()
        queue = assignment.queue
        assignment.delete()

        if not irr_data:
            DataQueue.objects.filter(data=datum, queue=queue).delete()
        else:
            process_irr_label(datum,label)
    if not irr_data:
        settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(datum))

def process_irr_label(data, label):
    '''
    This function checks if an irr datum has been labeled by enough people. if
    it has, then it will attempt to resolve the labels and record the irr history
    '''
    #get the number of labels for that data in the project
    labeled = DataLabel.objects.filter(data=data)
    project = data.project
    current_training_set = project.get_current_training_set()

    admin_queue = Queue.objects.get(project=project, admin=True, irr=False)
    #if there are >= labels than the project calls for
    if labeled.count() >= project.num_users_irr:
        #add all labels to IRRLog
        history_list = [IRRLog(data=data,
                               profile=d.profile,
                               label=d.label,
                               timestamp=d.timestamp) for d in labeled]
        with transaction.atomic():
            IRRLog.objects.bulk_create(history_list)

            #remove all labels from DataLabel and save in list
            labels = list(labeled.values_list('label', flat=True))

            DataLabel.objects.filter(data=data).delete()


            #check if the labels agree
            if len(set(labels)) == 1:
                #the data is no longer seen as irr (so it can be in the training set)
                Data.objects.filter(pk=data.pk).update(irr_ind=False)
                agree = True
                #if they do, add a new element to dataLabel with one label
                #by creator and remove from the irr queue
                DataLabel.objects.create(data=data,
                                         profile=project.creator,
                                         label=label,
                                         training_set = current_training_set,
                                         time_to_label=None,
                                         timestamp=timezone.now())
                DataQueue.objects.filter(data=data).delete()
            else:
                agree = False
                #if they don't, update the data into the admin queue
                DataQueue.objects.filter(data=data).update(queue=admin_queue)

        #update redis to reflect the queue changes
        irr_queue = Queue.objects.get(project=project, admin=False, irr=True)
        settings.REDIS.srem(redis_serialize_set(irr_queue), redis_serialize_data(data))

        if not agree:
            settings.REDIS.sadd(redis_serialize_set(admin_queue), redis_serialize_data(data))


def move_skipped_to_admin_queue(datum, profile, project):
    '''
    Remove the data from AssignedData and redis

    Change the assigned queue to the admin=True one for this project
    '''
    with transaction.atomic():
        #remove the data from the assignment table
        assignment = AssignedData.objects.get(data=datum,
                                                profile=profile)
        queue = assignment.queue
        assignment.delete()
        #change the queue to the admin one
        old_id = queue.id
        new_queue = Queue.objects.get(project=queue.project, admin=True, irr=False)
        DataQueue.objects.filter(data=datum, queue=queue).update(queue=new_queue)

    #remove the data from redis
    settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(datum))

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
        more_irr = True
        for i in range(num_assignments):

            #first try to get any IRR data
            if more_irr:
                assigned_datum = assign_datum(profile, project, irr=True)
                if assigned_datum is None:
                    #no irr data found
                    more_irr = False
                    assigned_datum = assign_datum(profile, project)
            else:
                #get normal data
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

    settings.REDIS.lpush(redis_serialize_queue(queue), redis_serialize_data(datum))


def batch_unassign(profile):
    '''
    Remove all of a profile's assignments and Re-add them to its respective
    queue in Redis.
    '''
    assignments = AssignedData.objects.filter(profile=profile)

    for a in assignments:
        unassign_datum(a.data, profile)


def save_data_file(df, project_pk):
    """Given the df used to create and save objects save just the data to a file.
        Make sure to count the number of files in directory assocaited with the
        project and save as next incremented file name

    Args:
        df: dataframe used to create and save data objects, contains `Text` column
            which has the text data
        project_pk: Primary key of the project
    Returns:
        file: The filepath to the saved datafile
    """
    num_proj_files = len([f for f in os.listdir(settings.PROJECT_FILE_PATH)
                          if f.startswith('project_'+str(project_pk))])
    fpath = os.path.join(settings.PROJECT_FILE_PATH, 'project_' + str(project_pk) + '_data_' + str(num_proj_files) + '.csv')

    df = df[['Text', 'Label']]
    df.to_csv(fpath, index=False)

    return fpath


def create_tfidf_matrix(data, max_df=0.95, min_df=0.05):
    """Create a TF-IDF matrix. Make sure to order the data by df_idx so that we
        can sync the data up again when training the model

    Args:
        data: List of data objs
    Returns:
        tf_idf_matrix: CSR-format tf-idf matrix
    """
    data_list = [d.text for d in data.order_by('df_idx')]
    vectorizer = TfidfVectorizer(max_df=max_df, min_df=min_df, stop_words='english')
    tf_idf_matrix = vectorizer.fit_transform(data_list)

    return tf_idf_matrix


def save_tfidf_matrix(matrix, project_pk):
    """Save tf-idf matrix to persistent volume storage defined in settings as
        TF_IDF_PATH

    Args:
        matrix: CSR-format tf-idf matrix
        project_pk: The project pk the data comes from
    Returns:
        file: The filepath to the saved matrix
    """
    fpath = os.path.join(settings.TF_IDF_PATH, str(project_pk) + '.npz')

    sparse.save_npz(fpath, matrix)

    return fpath


def load_tfidf_matrix(project_pk):
    """Load tf-idf matrix from persistent volume, otherwise None

    Args:
        project_pk: The project pk the data comes from
    Returns:
        matrix or None
    """
    fpath = os.path.join(settings.TF_IDF_PATH, str(project_pk) + '.npz')

    if os.path.isfile(fpath):
        return sparse.load_npz(fpath)
    else:
        raise ValueError('There was no tfidf matrix found for project: ' + str(project_pk))


def check_and_trigger_model(datum):
    """Given a recently assigned datum check if the project it belong to needs
       its model ran.  It the model needs to be run, start the model run and
       create a new project current_training_set

    Args:
        datum: Recently assigne Data object
    Returns:
        return_str: String to represent which path the function took
    """
    project = datum.project
    current_training_set = project.get_current_training_set()
    batch_size = project.labels.count() * 10
    labeled_data = DataLabel.objects.filter(data__project=project,
                                            training_set=current_training_set,
                                            data__irr_ind = False)
    labeled_data_count = labeled_data.count()
    labels_count = labeled_data.distinct('label').count()

    if current_training_set.celery_task_id != '':
        return_str = 'task already running'
    elif labeled_data_count >= batch_size:
        if labels_count < project.labels.count():
            queue = project.queue_set.get(admin=False, irr=False)
            fill_queue(queue = queue, orderby = 'random')
            return_str = 'random'
        else:
            task_num = tasks.send_model_task.delay(project.pk)
            current_training_set.celery_task_id = task_num
            current_training_set.save()
            return_str = 'model running'
    else:
        return_str = 'no trigger'

    return return_str


def train_and_save_model(project):
    """Given a project create a model, train it, and save the model pickle

    Args:
        project: The project to start training
    Returns:
        model: A model object
    """
    clf = LogisticRegression(class_weight='balanced', solver='lbfgs', multi_class='multinomial')
    tf_idf = load_tfidf_matrix(project.pk).A
    current_training_set = project.get_current_training_set()

    # In order to train need X (tf-idf vector) and Y (label) for every labeled datum
    # Order both X and Y by df_idx to ensure the tf-idf vector corresponds to the correct
    # label
    labeled_data = DataLabel.objects.filter(data__project=project)
    labeled_values = list(labeled_data.values_list('label', flat=True).order_by('data__df_idx'))
    labeled_indices = list(labeled_data.values_list('data__df_idx', flat=True).order_by('data__df_idx'))

    X = tf_idf[labeled_indices]
    Y = labeled_values
    clf.fit(X, Y)

    classes = [str(c) for c in clf.classes_]
    keys = ('precision', 'recall', 'f1')
    cv_predicts = cross_val_predict(clf, X, Y, cv=5)
    cv_accuracy = accuracy_score(Y, cv_predicts)
    metrics = precision_recall_fscore_support(Y, cv_predicts)
    metric_map = map(lambda x: dict(zip(classes, x)), metrics[:3])
    cv_metrics = dict(zip(keys, metric_map))

    fpath = os.path.join(settings.MODEL_PICKLE_PATH, 'project_' + str(project.pk) + '_training_' \
         + str(current_training_set.set_number) + '.pkl')

    joblib.dump(clf, fpath)

    model = Model.objects.create(pickle_path=fpath, project=project,
                                 training_set=current_training_set,
                                 cv_accuracy=cv_accuracy,
                                 cv_metrics=cv_metrics)

    return model


def least_confident(probs):
    """Least Confident
        x = 1 - p
        p is probability of highest probability class

    Args:
        probs: List of predicted probabilites
    Returns:
        x
    """
    if not isinstance(probs, np.ndarray):
        raise ValueError('Probs should be a numpy array')

    max_prob = max(probs)
    return 1 - max_prob


def margin_sampling(probs):
    """Margin Sampling
        x = p1 - p2
        p1 is probabiiity of highest probability class
        p2 is probability of lowest probability class
    Args:
        probs: List of predicted probabilities
    Returns:
        x
    """
    if not isinstance(probs, np.ndarray):
        raise ValueError('Probs should be a numpy array')

    probs[::-1].sort()  # https://stackoverflow.com/questions/26984414/efficiently-sorting-a-numpy-array-in-descending-order#answer-26984520
    return probs[0] - probs[1]


def entropy(probs):
    """Entropy - Uncertainty Sampling
        x = -sum(p * log(p))
        the sum is sumation across p's
    Args:
        probs: List of predicted probabilities
    Returns:
        x
    """
    if not isinstance(probs, np.ndarray):
        raise ValueError('Probs should be a numpy array')

    non_zero_probs = (p for p in probs if p > 0)

    total = 0
    for p in non_zero_probs:
        total += p * math.log10(p)

    return -total


def predict_data(project, model):
    """Given a project and its model, predict any unlabeled data and create
        Prediction objects for each.  There will be #label * #unlabeled_data
        predictions.  This is because we are saving the probability of each label
        for every data.

    Args:
        project: Project object
        model: Model object
    Returns:
        predictions: List of DataPrediction objects
    """
    clf = joblib.load(model.pickle_path)
    tf_idf = load_tfidf_matrix(project.pk).A

    # In order to predict need X (tf-idf vector) for every unlabeled datum. Order
    # X by df_idx to ensure the tf-idf vector corresponds to the correct datum
    unlabeled_data = project.data_set.filter(datalabel__isnull=True).order_by('df_idx')
    unlabeled_indices = unlabeled_data.values_list('df_idx', flat=True).order_by('df_idx')

    X = tf_idf[unlabeled_indices]
    predictions = clf.predict_proba(X)

    label_obj = [Label.objects.get(pk=label) for label in clf.classes_]

    bulk_predictions = []
    for datum, prediction in zip(unlabeled_data, predictions):
        # each prediction is an array of probabilities.  Each index in that array
        # corresponds to the label of the same index in clf.classes_
        for p, label in zip(prediction, label_obj):
            bulk_predictions.append(DataPrediction(data=datum, model=model,
                                       label=label,
                                       predicted_probability=p))

        # Need to crate uncertainty object so fill_queue can sort by one of the metrics
        lc = least_confident(prediction)
        ms = margin_sampling(prediction)
        e = entropy(prediction)

        DataUncertainty.objects.create(data=datum,
                                       model=model,
                                       least_confident=lc,
                                       margin_sampling=ms,
                                       entropy=e)

    prediction_objs = DataPrediction.objects.bulk_create(bulk_predictions)

    return prediction_objs

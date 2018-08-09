import random
import redis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.externals import joblib
from scipy import sparse
import os
import math
import numpy as np
import hashlib
import pandas as pd
import pickle
import statsmodels.stats.inter_rater as raters
from collections import defaultdict
from itertools import combinations
from django.utils import timezone

# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
# Disable warning for false positive warning that should only trigger on chained assignment
pd.options.mode.chained_assignment = None  # default='warn'
from celery.result import AsyncResult

from django.db import transaction, connection
from django.db.models import Count, Value, IntegerField, F, Max, Min
from django.db.utils import ProgrammingError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from core.models import (Project, Data, Queue, DataQueue, Profile, Label,
                         AssignedData, DataLabel, Model, DataPrediction,
                         DataUncertainty, TrainingSet, RecycleBin, IRRLog, ProjectPermissions)
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
        if isinstance(obj, int):
            obj = str(obj)
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


def create_project(name, creator, percentage_irr=10,num_users_irr=2):
    '''
    Create a project with the given name and creator.
    '''
    proj = Project.objects.create(name=name, creator=creator,
                                   percentage_irr = percentage_irr,
                                    num_users_irr = num_users_irr)
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

    #check that the data is not already in the system and drop duplicates
    df = df.loc[~df['hash'].isin(list(Data.objects.filter(project=project).values_list("hash",flat=True)))]
    if len(df) == 0:
        return []
    # Limit the number of rows to 2mil for the entire project
    num_existing_data = Data.objects.filter(project=project).count()
    if num_existing_data >= 2000000:
        return []

    df = df[:2000000- num_existing_data]
    #if there is no ID column already, add it and hash it
    df.reset_index(drop=True, inplace=True)
    if 'ID' not in df.columns:
        #should add to what already exists
        df["ID"] = [x + num_existing_data for x in list(df.index.values)]
        df["id_hash"] = df["ID"].astype(str).apply(md5_hash)
    else:
        #get the hashes from existing identifiers. Check that the new identifiers do not overlap
        existing_hashes = Data.objects.filter(project=project).values_list('upload_id_hash',flat=True)
        df = df.loc[~df['id_hash'].isin(existing_hashes)]
        if len(df) == 0:
            return []


    # Create the data objects
    df['object'] = df.apply(lambda x: Data(text=x['Text'], project=project,
                                            hash=x['hash'],
                                            upload_id=x['ID'], upload_id_hash = x['id_hash']), axis=1)
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
        batch_size [default: number of labels * 10]
        num_coders [creator, admins, coders]
    Returns:
        queue_length
    """
    return math.ceil(batch_size/num_coders) * num_coders + math.ceil(batch_size/num_coders) * (num_coders - 1)


def add_queue(project, length, type="normal", profile=None):
    '''
    Add a queue of the given length to the given project.  If a profile is provided,
    assign the queue to that profile.

    Return the created queue.
    '''
    return Queue.objects.create(length=length, project=project, profile=profile, type=type)


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

    recycled_data = RecycleBin.objects.filter(data__project=queue.project).values_list('data__pk',flat=True)
    data_filters = {
        'project': queue.project,
        'labelers': None,
        'queues': None,
        'irr_ind': False
    }

    eligible_data = Data.objects.filter(**data_filters).exclude(pk__in=recycled_data)

    cte_sql, cte_params = eligible_data.query.sql_with_params()

    #get the join clause that controls how the data is selected
    join_clause = get_join_clause(orderby, queue)

    #First process the IRR data
    if irr_queue:
        #if the irr queue is given, want to fill it with a given percent of
        #the batch size
        num_irr = math.ceil(batch_size * (irr_percent/100))
        num_elements = len(DataQueue.objects.filter(queue=irr_queue))
        queue_size = irr_queue.length

        #get the number of elements to add to the irr queue
        irr_sample_size_sql, irr_sample_size_params = get_queue_size_params(irr_queue,queue_size, num_elements, num_irr, irr_queue)
        #get the sql for adding the elements
        irr_sql = generate_sql_for_fill_queue(irr_queue,ORDERBY_VALUE[orderby],join_clause, cte_sql, irr_sample_size_sql)

        with connection.cursor() as c:
            c.execute(irr_sql, (*cte_params, *irr_sample_size_params))

        data_ids = []
        with transaction.atomic():
            irr_data = DataQueue.objects.filter(queue=irr_queue.pk)
            for d in irr_data:
                data_ids.append(d.data.pk)
            Data.objects.filter(pk__in=data_ids).update(irr_ind=True)

        sync_redis_objects(irr_queue, orderby)

        #get new eligible data by filtering out what was just chosen
        eligible_data = eligible_data.exclude(pk__in=data_ids)
        cte_sql, cte_params = eligible_data.query.sql_with_params()

    #get the remaining space in the normal queue
    non_irr_batch_size = math.ceil(batch_size * ((100 - irr_percent)/100))
    num_in_queue = len(DataQueue.objects.filter(queue=queue))
    queue_size = queue.length
    #if there is not much space or we are not filling the irr queue, just
    #fill the normal queue to the top
    sample_size_sql, sample_size_params = get_queue_size_params(queue,queue_size, num_in_queue, non_irr_batch_size, irr_queue)

    sql = generate_sql_for_fill_queue(queue, ORDERBY_VALUE[orderby], join_clause, cte_sql, sample_size_sql)

    with connection.cursor() as c:
        c.execute(sql, (*cte_params, *sample_size_params))

    sync_redis_objects(queue, orderby)

def generate_sql_for_fill_queue(queue, orderby_value, join_clause, cte_sql, size_sql):
    '''
    This function merely takes the given paramters and returns an sql query
    to execute for filling the queue
    '''
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
        orderby_value=orderby_value,
        sample_size_sql= size_sql)
    return sql

def get_join_clause(orderby, queue):
    '''
    This function generates the join clause used to fill queues
    '''
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
    return join_clause

def get_queue_size_params(queue,queue_size, num_in_queue, batch_size, irr_queue):
    '''
    Get the sql parameters for the number of items to add to the queue
    '''
    #if there is less space in the queue than the default number of
    #elements to add, or we are trying to fill the queue to the top
    #(irr_queue=None in the second case)
    if (queue_size - num_in_queue < batch_size) or not(irr_queue):
        sample_size_sql, sample_size_params = (Queue.objects.filter(pk=queue.pk)
                                                .annotate(sample_size=F('length') - Count('data'))
                                                .values('sample_size')
                                                .query.sql_with_params())
    else:
        #just add the number requested (some percent of the batch size)
        sample_size_sql, sample_size_params = (Queue.objects.filter(pk=queue.pk)
                                                .annotate(sample_size=Value(batch_size, IntegerField()))
                                                .values('sample_size')
                                                .query.sql_with_params())
    return sample_size_sql, sample_size_params


def pop_first_nonempty_queue(project, profile=None, type="normal"):
    '''
    Determine which queues are eligible to be popped (and in what order)
    and pass them into redis to have the first nonempty one popped.
    Return a (queue, data item) tuple if one was found; return a (None, None)
    tuple if not.
    '''
    if profile is not None:
        # Use priority to ensure we set profile queues above project queues
        # in the resulting list; break ties by pk
        profile_queues = project.queue_set.filter(profile=profile, type=type)
    else:
        profile_queues = Queue.objects.none()
    profile_queues = profile_queues.annotate(priority=Value(1, IntegerField()))

    project_queues = (project.queue_set.filter(profile=None, type=type)
                      .annotate(priority=Value(2, IntegerField())))

    eligible_queue_ids = [redis_serialize_queue(queue) for queue in
                          (profile_queues.union(project_queues)
                           .order_by('priority', 'pk'))]


    if type == "irr":
        for queue_id in eligible_queue_ids:
            queue = redis_parse_queue(queue_id.encode())

            #first get the assigned data that was already labeled, or data already assigned
            labeled_irr_data = DataLabel.objects.filter(profile=profile).values_list('data',flat=True)
            assigned_data = AssignedData.objects.filter(profile=profile, queue=queue).values_list('data',flat=True)
            skipped_data = IRRLog.objects.filter(profile=profile,label__isnull=True).values_list('data',flat=True)
            assigned_unlabeled = DataQueue.objects.filter(queue=queue).exclude(data__in=labeled_irr_data).exclude(data__in=assigned_data).exclude(data__in=skipped_data)

            #if there are no elements, return none
            if len(assigned_unlabeled) == 0:
                return (None, None)
            else:
                #else, get the first element off the group and return it
                datum = Data.objects.get(pk=assigned_unlabeled[0].data.pk)
                return (queue, datum)
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
                                .filter(profile=profile, type="normal")
                                .annotate(
                                    data_count=Count('data'))
                                .filter(data_count__gt=0))

        if len(nonempty_profile_queues) > 0:
            first_nonempty_queue = nonempty_profile_queues.first()

    # If we didn't find a profile queue, check project queues
    if first_nonempty_queue is None:
        nonempty_queues = (project.queue_set
                           .filter(profile=None, type="normal")
                           .annotate(
                               data_count=Count('data'))
                           .filter(data_count__gt=0))

        if len(nonempty_queues) > 0:
            first_nonempty_queue = nonempty_queues.first()

    return first_nonempty_queue


def assign_datum(profile, project, type="normal"):
    '''
    Given a profile and project, figure out which queue to pull from;
    then pop a datum off that queue and assign it to the profile.
    '''
    with transaction.atomic():
        queue, datum = pop_first_nonempty_queue(project, profile=profile, type=type)
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

def skip_data(datum, profile):
    '''
    Record that a given datum has been skipped
    '''
    project = datum.project
    queue = Queue.objects.get(project=project,type="normal")

    IRRLog.objects.create(data=datum, profile=profile, label = None, timestamp = timezone.now())
    num_history = IRRLog.objects.filter(data=datum).count()
    #if the datum is irr or processed irr, dont add to admin queue yet
    if datum.irr_ind or num_history > 0:
        #if the IRR history has more than the needed number of labels , it is
        #already processed so don't do anything else
        if num_history <= project.num_users_irr:
            process_irr_label(datum, None)

        #unassign the skipped item
        assignment = AssignedData.objects.get(data=datum,profile=profile)
        assignment.delete()
    else:
        # Make sure coder still has permissions before labeling data
        if project_extras.proj_permission_level(project, profile) > 0:
            move_skipped_to_admin_queue(datum, profile, project)

def label_data(label, datum, profile, time):
    '''
    Record that a given datum has been labeled; remove its assignment, if any.

    Remove datum from DataQueue and its assocaited redis set.
    '''
    current_training_set = datum.project.get_current_training_set()
    project = datum.project
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
            num_history = IRRLog.objects.filter(data=datum).count()
            #if the IRR history has more than the needed number of labels , it is
            #already processed so just add this label to the history.
            if num_history >= datum.project.num_users_irr:
                IRRLog.objects.create(data=datum, profile=profile, label=label, timestamp = timezone.now())
                DataLabel.objects.get(data=datum,profile=profile).delete()
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
    skipped = IRRLog.objects.filter(label__isnull=True, data=data)
    project = data.project
    current_training_set = project.get_current_training_set()

    admin_queue = Queue.objects.get(project=project, type="admin")
    #if there are >= labels or skips than the project calls for
    if (labeled.count() + skipped.count()) >= project.num_users_irr:
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
            if len(set(labels)) == 1 and skipped.count() == 0:
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
        irr_queue = Queue.objects.get(project=project, type="irr")
        settings.REDIS.srem(redis_serialize_set(irr_queue), redis_serialize_data(data))

        if not agree:
            settings.REDIS.sadd(redis_serialize_set(admin_queue), redis_serialize_data(data))


def cohens_kappa(project):
    '''
    Takes in the irr log data and calculates cohen's kappa
    NOTE: this should only be used if the num_users_irr = 2
    https://onlinecourses.science.psu.edu/stat509/node/162/
    https://en.wikipedia.org/wiki/Cohen%27s_kappa
    '''
    irr_data = set(IRRLog.objects.values_list('data', flat=True))

    agree = 0

    #initialize the dictionary
    rater1_rater2_dict = {}
    label_list = list(Label.objects.filter(project=project).values_list('name',flat=True))
    label_list.append("skip")
    for label1 in label_list:
        rater1_rater2_dict[label1] = {}
        for label2 in label_list:
            rater1_rater2_dict[label1][label2] = 0

    num_data = 0
    labels_seen = set()
    for d in irr_data:
        d_log = IRRLog.objects.filter(data=d,data__project=project)
        labels = list(set(d_log.values_list('label',flat=True)))
        labels_seen = labels_seen | set(labels)
        #get the percent agreement between the users  = (num agree)/size_data
        if d_log.count() < 2:
            #don't use this datum, it isn't processed yet
            continue
        num_data += 1
        if len(labels) == 1:
            if labels[0] != None:
                agree += 1
        if d_log[0].label == None:
            label1 = "skip"
        else:
            label1 = d_log[0].label.name

        if d_log[1].label == None:
            label2 = "skip"
        else:
            label2 = d_log[1].label.name


        rater1_rater2_dict[label1][label2] +=1
    if num_data == 0:
        #there is no irr data, so just return bad values
        raise ValueError('No irr data')

    if len(labels_seen) < 2:
        raise ValueError('Need at least two labels represented')

    kappa = raters.cohens_kappa(np.asarray(pd.DataFrame(rater1_rater2_dict)),return_results=False)

    p_o = agree / num_data
    return kappa, p_o

def fleiss_kappa(project):
    '''
    Takes in the irr log data and calculates fleiss's kappa
    Code modified from:
    https://gist.github.com/skylander86/65c442356377367e27e79ef1fed4adee
    Equations from: https://en.wikipedia.org/wiki/Fleiss%27_kappa
    '''
    irr_data = set(IRRLog.objects.values_list('data', flat=True))


    label_list = list(Label.objects.filter(project=project).values_list('name',flat=True))
    label_list.append(None)
    #number of labels in the project +1 for skipping
    k = len(label_list)
    #n is the number of labelers
    n = project.num_users_irr
    agree = 0
    data_label_dict = []
    num_data = 0
    for d in irr_data:
        d_data_log = IRRLog.objects.filter(data=d,data__project=project)

        if d_data_log.count() < n:
            #don't use this datum, it isn't processed yet
            continue
        elif d_data_log.count() > n:
            #grab only the first few elements if there were extra labelers
            d_data_log = d_data_log[:n]
        num_data += 1
        labels = list(set(d_data_log.values_list('label',flat=True)))
        #accumulate the percent agreement
        if len(labels) == 1:
            if labels[0] != None:
                agree += 1

        label_count_dict = {}
        for l in label_list:
            if l == None:
                l_label = "skip"
            else:
                l_label = str(l)
            label_count_dict[l_label] = len(d_data_log.filter(label__name = l))

        data_label_dict.append(label_count_dict)

    if num_data == 0:
        #there is no irr data, so just return bad values
        raise ValueError('No irr data')

    kappa = raters.fleiss_kappa(np.asarray(pd.DataFrame(data_label_dict)))

    return kappa, agree/num_data

def perc_agreement_table_data(project):
    '''
    Takes in the irrlog and finds the pairwise percent agreement
    '''
    irr_data = set(IRRLog.objects.filter(data__project=project).values_list('data', flat=True))

    user_list = [str(Profile.objects.get(pk=x)) for x in list(ProjectPermissions.objects.filter(project=project).values_list('profile',flat=True))]
    user_list.append(str(project.creator))
    user_pk_list = list(ProjectPermissions.objects.filter(project=project).values_list('profile__pk',flat=True))
    user_pk_list.append(project.creator.pk)
    #get all possible pairs of users
    user_combinations = combinations(user_list,r=2)
    data_choices = []

    for d in irr_data:
        d_log = IRRLog.objects.filter(data=d,data__project=project)
        labels = list(set(d_log.values_list('label',flat=True)))
        #get the percent agreement between the users  = (num agree)/size_data
        if d_log.count() < 2:
            #don't use this datum, it isn't processed yet
            continue
        temp_dict = {}
        for user in user_pk_list:
            if d_log.filter(profile=user).count() == 0:
                temp_dict[str(Profile.objects.get(pk=user))] = np.nan
            else:
                d = d_log.get(profile=user)
                if d.label == None:
                    name = "Skip"
                else:
                    name = d.label.name
                temp_dict[str(d.profile)] = name
        data_choices.append(temp_dict)
    #If there is no data, just return nothing
    if len(data_choices) == 0:
        user_agree = []
        for pair in user_combinations:
            user_agree.append({"First Coder":pair[0],"Second Coder":pair[1],"Percent Agreement":"No samples"})
        return user_agree

    choice_frame = pd.DataFrame(data_choices)
    user_agree = []
    for pair in user_combinations:
        #get the total number they both edited
        p_total = len(choice_frame[[pair[0],pair[1]]].dropna(axis=0))

        #get the elements that were labeled by both and not skipped
        choice_frame2 = choice_frame[[pair[0],pair[1]]].replace("Skip", np.nan).dropna(axis=0)

        #fill the na's so if they are both na they aren't equal
        p_agree = np.sum(np.equal(choice_frame2[pair[0]],choice_frame2[pair[1]]))

        if p_total > 0:
            user_agree.append({"First Coder":pair[0],"Second Coder":pair[1],"Percent Agreement":str(100*round(p_agree/p_total,3))+"%"})
        else:
            user_agree.append({"First Coder":pair[0],"Second Coder":pair[1],"Percent Agreement":"No samples"})
    return user_agree

def irr_heatmap_data(project):
    '''
    Takes in the irrlog and formats the data to be usable in the irr heatmap

    '''
    #get the list of users and labels for this project
    user_list = list(ProjectPermissions.objects.filter(project=project).values_list('profile__user',flat=True))
    user_list.append(project.creator.pk)
    label_list = list(Label.objects.filter(project=project).values_list('name',flat=True))
    label_list.append("Skip")

    irr_data = set(IRRLog.objects.values_list('data', flat=True))


    #Initialize the dictionary of dictionaries to use for the heatmap later
    user_label_counts = {}
    for user1 in user_list:
        for user2 in user_list:
            user_label_counts[str(user1)+"_"+str(user2)] = {}
            for label1 in label_list:
                user_label_counts[str(user1)+"_"+str(user2)][str(label1)] = {}
                for label2 in label_list:
                    user_label_counts[str(user1)+"_"+str(user2)][str(label1)][str(label2)] = 0

    for data_id in irr_data:
        #iterate over the data and count up labels
        data_log_list = IRRLog.objects.filter(data=data_id,data__project=project)
        small_user_list = data_log_list.values_list('profile__user',flat=True)
        for user1 in small_user_list:
            for user2 in small_user_list:
                user_combo = str(user1)+"_"+str(user2)
                label1 = data_log_list.get(profile__pk = user1).label
                label2 = data_log_list.get(profile__pk = user2).label
                user_label_counts[user_combo][str(label1).replace("None","Skip")][str(label2).replace("None","Skip")] +=1
    #get the results in the final format needed for the graph
    end_data = {}
    for user_combo in user_label_counts:
        end_data_list = []
        for label1 in user_label_counts[user_combo]:
            for label2 in user_label_counts[user_combo][label1]:
                end_data_list.append({"label1":label1,"label2":label2,"count":user_label_counts[user_combo][label1][label2]})
        end_data[user_combo] = end_data_list

    return end_data


def move_skipped_to_admin_queue(datum, profile, project):
    '''
    Remove the data from AssignedData and redis

    Change the assigned queue to the admin one for this project
    '''
    with transaction.atomic():
        #remove the data from the assignment table
        assignment = AssignedData.objects.get(data=datum,
                                                profile=profile)
        queue = assignment.queue
        assignment.delete()
        #change the queue to the admin one
        old_id = queue.id
        new_queue = Queue.objects.get(project=queue.project, type="admin")
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
                assigned_datum = assign_datum(profile, project, type="irr")
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

def save_codebook_file(data, project_pk):
    """Given the django data file, save it as the codebook for that project
    make sure to overwrite any project that is already there/

    """
    date = timezone.now().strftime('%m_%d_%y__%H_%M_%S')
    fpath = os.path.join(settings.CODEBOOK_FILE_PATH, 'project_' + str(project_pk) + '_codebook'+date+'.pdf')
    with open(fpath, "wb") as outputFile:
        outputFile.write(data.read())
    return fpath.replace("/data/code_books/","")

def create_tfidf_matrix(data, max_df=0.95, min_df=0.05):
    """Create a TF-IDF matrix. Make sure to order the data by upload_id_hash so that we
        can sync the data up again when training the model

    Args:
        data: List of data objs
    Returns:
        tf_idf_matrix: CSR-format tf-idf matrix
    """
    id_list = list(data.values_list('upload_id', flat=True).order_by('upload_id_hash'))
    data_list = list(data.values_list('text', flat=True).order_by('upload_id_hash'))

    vectorizer = TfidfVectorizer(max_df=max_df, min_df=min_df, stop_words='english')
    tf_idf_matrix = vectorizer.fit_transform(data_list)

    new_dict = dict(zip(id_list, np.matrix.tolist(sparse.csr_matrix.todense(tf_idf_matrix))))

    return new_dict


def save_tfidf_matrix(matrix, project_pk):
    """Save tf-idf matrix to persistent volume storage defined in settings as
        TF_IDF_PATH

    Args:
        matrix: CSR-format tf-idf matrix
        project_pk: The project pk the data comes from
    Returns:
        file: The filepath to the saved matrix
    """
    fpath = os.path.join(settings.TF_IDF_PATH, str(project_pk) + '.pkl')
    pickle.dump(matrix, open(fpath, "wb"))

    return fpath


def load_tfidf_matrix(project_pk):
    """Load tf-idf matrix from persistent volume, otherwise None

    Args:
        project_pk: The project pk the data comes from
    Returns:
        matrix or None
    """
    fpath = os.path.join(settings.TF_IDF_PATH, str(project_pk) + '.pkl')

    if os.path.isfile(fpath):
        return pickle.load(open(fpath,"rb"))#sparse.load_npz(fpath)
    else:
        raise ValueError('There was no tfidf matrix found for project: ' + str(project_pk))


def check_and_trigger_model(datum, profile=None):
    """Given a recently assigned datum check if the project it belong to needs
       its model ran.  It the model needs to be run, start the model run and
       create a new project current_training_set

    Args:
        datum: Data object (may or may not be labeled)
    Returns:
        return_str: String to represent which path the function took
    """
    project = datum.project
    current_training_set = project.get_current_training_set()
    batch_size = project.batch_size
    labeled_data = DataLabel.objects.filter(data__project=project,
                                            training_set=current_training_set,
                                            data__irr_ind = False)
    labeled_data_count = labeled_data.count()
    labels_count = labeled_data.distinct('label').count()

    #if both the normal and irr queue are empty or the user
    #has labeled all of the irr
    if profile:
        queue = Queue.objects.get(project=project,type="normal")
        irr_queue = Queue.objects.get(project=project,type="irr")
        queue_count = DataQueue.objects.filter(queue=queue).count()
        #get the number of items that the profile has not labeled/skipped in irr
        irr_data = DataQueue.objects.filter(queue=irr_queue)
        irr_count = 0
        for d in irr_data:
            #if they have already labeled it
            if len(DataLabel.objects.filter(data=d.data,profile=profile)) > 0:
                continue
            #if they skipped it
            if len(IRRLog.objects.filter(data=d.data,profile=profile)) > 0:
                continue
            irr_count += 1
    else:
        #this data was not labeled, so there isn't a profile attached
        queue_count = 1
        irr_count = 1

    if current_training_set.celery_task_id != '':
        return_str = 'task already running'
    elif labeled_data_count >= batch_size:
        if labels_count < project.labels.count() or project.classifier is None:
            queue = project.queue_set.get(type="normal")
            fill_queue(queue = queue, orderby = 'random', batch_size=batch_size)
            return_str = 'random'
        else:
            task_num = tasks.send_model_task.delay(project.pk)
            current_training_set.celery_task_id = task_num
            current_training_set.save()
            return_str = 'model running'
    elif (irr_count == 0) and (queue_count == 0):
        #check if the user has any unlabeled stuff left. If not,
        #we need to refil the queue

        #if there is a model, use the orderby of the project, otherwise random
        if len(Model.objects.filter(project=project)) > 0:
            fill_queue(queue=queue, orderby = project.learning_method,
                       irr_queue = irr_queue, irr_percent = project.percentage_irr,
                       batch_size = batch_size )
            return_str = project.learning_method
        else:
            fill_queue(queue=queue, orderby = 'random',
                       irr_queue = irr_queue, irr_percent = project.percentage_irr,
                       batch_size = batch_size )
            return_str = 'random'
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
    if project.classifier == "logistic regression":
        clf = LogisticRegression(class_weight='balanced', solver='lbfgs', multi_class='multinomial')
    elif project.classifier == "svm":
        clf = SVC(probability=True)
    elif project.classifier == "random forest":
        clf = RandomForestClassifier()
    elif project.classifier == "gnb":
        clf = GaussianNB()
    else:
        raise ValueError('There was no valid classifier for project: ' + str(project.pk))
    tf_idf = load_tfidf_matrix(project.pk)

    current_training_set = project.get_current_training_set()

    # In order to train need X (tf-idf vector) and Y (label) for every labeled datum
    # Order both X and Y by upload_id_hash to ensure the tf-idf vector corresponds to the correct
    # label

    labeled_data = DataLabel.objects.filter(data__project=project)
    unique_ids = list(labeled_data.values_list("data__upload_id", flat=True).order_by('data__upload_id_hash'))
    labeled_values = list(labeled_data.values_list('label', flat=True).order_by('data__upload_id_hash'))

    X = [tf_idf[id] for id in unique_ids]
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

def get_labeled_data(project):
    """Given a project, get the list of labeled data

    Args:
        project: Project object
    Returns:
        data: a list of the labeled data
    """
    project_labels = Label.objects.filter(project=project)
    #get the data labels
    data = []
    for label in project_labels:
        labeled_data = DataLabel.objects.filter(label=label)
        for d in labeled_data:
            temp = {}
            temp['ID'] = d.data.upload_id
            temp['Text'] = d.data.text
            temp['Label'] = label.name
            data.append(temp)
    return data

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
    tf_idf = load_tfidf_matrix(project.pk)

    # In order to predict need X (tf-idf vector) for every unlabeled datum. Order
    # X by upload_id_hash to ensure the tf-idf vector corresponds to the correct datum
    recycle_data = RecycleBin.objects.filter(data__project=project).values_list('pk',flat=True)
    unlabeled_data = project.data_set.filter(datalabel__isnull=True).exclude(pk__in=recycle_data).order_by('upload_id_hash')
    unique_ids = list(unlabeled_data.values_list("upload_id", flat=True).order_by('upload_id_hash'))

    #get the list of all data sorted by identifier
    X = [tf_idf[id] for id in unique_ids]
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

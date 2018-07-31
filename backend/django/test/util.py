import csv
import pandas as pd

from core.management.commands.seed import (SEED_FILE_PATH)
from core.models import Queue
from core.util import md5_hash

def assert_obj_exists(model, filter_):
    '''
    See if an instance of the given model matching the given filter
    dict exists.
    '''
    matching_count = model.objects.filter(**filter_).count()
    assert matching_count > 0, "{} matching filter {} " \
        "does not exist. ".format(model.__name__, filter_)


def assert_redis_matches_db(test_redis):
    '''
    Make sure all nonempty queues are present in the redis DB and
    have the correct amount of data, as determined by the DB.
    '''
    for q in Queue.objects.all():
        data_count = q.data.count()

        if data_count > 0:
            assert test_redis.exists('queue:'+str(q.pk))
            assert test_redis.llen('queue:'+str(q.pk)) == data_count
            assert test_redis.exists('set:'+str(q.pk))
            assert test_redis.scard('set:'+str(q.pk)) == data_count
        else:
            # Empty lists don't exist in redis
            assert not test_redis.exists('queue:'+str(q.pk))
            assert not test_redis.exists('set:'+str(q.pk))


def read_test_data_api(file=SEED_FILE_PATH):
    '''
    Read the test data from its file and store as list of dicts.  Used for API
    tests.
    '''
    with open(file) as f:
        return [{'Text': d['Text'], 'Label': d['Label']} for d in csv.DictReader(f)]

def read_test_data_backend(file=SEED_FILE_PATH):
    '''
    Read the test data from its file and store as dataframe.  Used for backend
    tests.
    '''
    return pd.read_csv(file)

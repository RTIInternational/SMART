import csv

from core.management.commands.seed import (SEED_FILE_PATH)
from core.models import Queue

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
        else:
            # Empty lists don't exist in redis
            assert not test_redis.exists('queue:'+str(q.pk))


def read_test_data(file=SEED_FILE_PATH):
    '''
    Read the test data from its file, as we'd expect to find
    it in the database.
    '''
    with open(file) as f:
        return [{'Text': d['Text'], 'Label': d['Label']} for d in csv.DictReader(f)]

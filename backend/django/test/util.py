import celery
import csv

from core.management.commands.seed import (SEED_FILE_PATH)

@celery.shared_task
def dummy_task():
    return 'Test task complete'

def read_test_data():
    '''
    Read the test data from its file, as we'd expect to find
    it in the database.
    '''
    with open(SEED_FILE_PATH) as f:
        return [{'text': d['Tweet'], 'label': d['Stance']} for d in csv.DictReader(f)]

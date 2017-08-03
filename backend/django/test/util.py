import celery

@celery.shared_task
def dummy_task():
    return 'Test task complete'

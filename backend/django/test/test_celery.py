import util

def test_celery():
    result = util.dummy_task.delay().get()
    assert result == 'Test task complete'

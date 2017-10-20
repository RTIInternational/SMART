from core import tasks

def test_celery():
    result = tasks.send_test_task.delay().get()
    assert result == 'Test Task Complete'


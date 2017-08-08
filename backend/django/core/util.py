from core.models import (Project, Data, Queue)

def create_project(project_attrs, data):
    '''
    Create a project with the given attributes and data,
    initializing a project queue and returning the created
    project.

    Data should be an array of strings.
    '''
    project = Project(**project_attrs)
    project.save()

    bulk_data = (Data(text=d, project=project) for d in data)
    Data.objects.bulk_create(bulk_data)

    return project

def add_queue(project, length, user=None):
    '''
    Add a queue of the given length to the given project.  If a user is provided,
    assign the queue to that user.

    Return the created queue.
    '''
    queue = Queue(length=length, project=project, user=user)
    queue.save()

    return queue

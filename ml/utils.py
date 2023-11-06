import importlib
import models


def encode(project, text):
    if project in list(models.models.keys()):
        return models.models[project].encode(text)
    return models.models["default"].encode(text)


def reload():
    importlib.reload(models)

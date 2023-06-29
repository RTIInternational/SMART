from sentence_transformers import SentenceTransformer

import os
import paths

default = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")

models = {"default": default}

projects = filter(
    lambda x: (os.path.isfile(f"{paths.MODELS}/{x}/config.json")),
    filter(os.path.isdir, os.listdir(paths.MODELS)),
)

for project in projects:
    models[project] = SentenceTransformer(paths.path_models(project))

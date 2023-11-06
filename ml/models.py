from sentence_transformers import SentenceTransformer

import os
import paths

default = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")

models = {"default": default}

for project in os.listdir(paths.MODELS):
    models[project] = SentenceTransformer(paths.path_models(project))

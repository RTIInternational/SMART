from django.core.cache import cache
from sentence_transformers import util

import json
import requests


def cache_embeddings(project_pk, embeddings):
    cache.set(project_pk, embeddings)


def compare(embedding, embeddings):
    cosine_scores = util.pytorch_cos_sim(embedding, embeddings)
    values, indicies = cosine_scores[0].topk(5)
    return {"indices": indicies, "values": values}


def get_embeddings(project_pk):
    return cache.get(project_pk)


def encode(text, project):
    return json.loads(
        requests.get(
            f"http://ml:8001/encode/{project}",
            json={"text": text},
            headers={"Content-Type": "application/json"},
        ).content
    )["results"]

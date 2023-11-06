import json

import requests
from django.core.cache import cache
from sentence_transformers import util


def cache_embeddings(project, embeddings):
    cache.set(project, embeddings)


def compare(embedding, embeddings):
    cosine_scores = util.pytorch_cos_sim(embedding, embeddings)
    values, indicies = cosine_scores[0].topk(5)
    return {"indices": indicies, "values": values}


def get_embeddings(project):
    return cache.get(project)


def encode(project, text):
    return json.loads(
        requests.get(
            f"http://ml:8001/encode/{project}",
            json={"text": text},
            headers={"Content-Type": "application/json"},
        ).content
    )["results"]


def train(project, file):
    return json.loads(
        requests.post(f"http://ml:8001/train/{project}", files={"file": file}).content
    )

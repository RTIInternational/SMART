from sentence_transformers import SentenceTransformer, util

# Model can be found here: https://www.sbert.net/docs/pretrained_models.html
# Model Card: https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1
embeddings_model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")


def getEmbeddings(strings):
    return embeddings_model.encode(strings)


def getTop5Embeddings(text_embedding, embeddings):
    cosine_scores = util.pytorch_cos_sim(text_embedding, embeddings)
    values, indices = cosine_scores[0].topk(5)
    return indices

---
pipeline_tag: sentence-similarity
tags:
- sentence-transformers
- feature-extraction
- sentence-similarity
---

# Smart Embeddings Model

This is a [sentence-transformers](https://www.SBERT.net) model: It maps sentences & paragraphs to a 384 dimensional dense vector space and can be used for tasks like clustering or semantic search.

## Purpose for Making the Model

The purpose of this model is to blacklist some specific matches and create mappings to certain abbreviations needed for the project.

## Building the Model

- The model was built with: https://github.com/dsteedRTI/csv-to-embeddings-model
- Sbert Model can be found here: https://www.sbert.net/docs/pretrained_models.html
- Sbert Model Card: https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1


## Usage (Sentence-Transformers)

Using this model becomes easy when you have [sentence-transformers](https://www.SBERT.net) installed:

```
pip install -U sentence-transformers
```

Then you can use the model like this:

```python
from sentence_transformers import SentenceTransformer
sentences = ["This is an example sentence", "Each sentence is converted"]

# Use path to model
model_path = "core/smart_embeddings_model"
embeddings_model = SentenceTransformer(model_path)
embeddings = model.encode(sentences)
print(embeddings)
```



## Evaluation Results

The model was evaluated on top of the [multi-qa-mpnet-base-dot-v1](https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1) model. Specific blacklists and abbreviations were then loaded into the model to create a more accurate model for this particular project.


## Training
The model was trained with the parameters:

**DataLoader**:

`torch.utils.data.dataloader.DataLoader` of length 93 with parameters:
```
{'batch_size': 16, 'sampler': 'torch.utils.data.sampler.RandomSampler', 'batch_sampler': 'torch.utils.data.sampler.BatchSampler'}
```

**Loss**:

`sentence_transformers.losses.CosineSimilarityLoss.CosineSimilarityLoss` 

Parameters of the fit()-Method:
```
{
    "epochs": 1,
    "evaluation_steps": 0,
    "evaluator": "NoneType",
    "max_grad_norm": 1,
    "optimizer_class": "<class 'transformers.optimization.AdamW'>",
    "optimizer_params": {
        "lr": 2e-05
    },
    "scheduler": "WarmupLinear",
    "steps_per_epoch": null,
    "warmup_steps": 100,
    "weight_decay": 0.01
}
```


## Full Model Architecture
```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 512, 'do_lower_case': False}) with Transformer model: BertModel 
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False})
  (2): Normalize()
)
```

## Citing & Authors

- [dsteedRTI](https://github.com/dsteedRTI)
- [peridoteagle](https://github.com/peridoteagle)
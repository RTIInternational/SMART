from sentence_transformers import InputExample, losses
from torch.utils.data import DataLoader

import csv
import models
import paths


def train(project):
    project_path_csv = paths.path_csv(project)
    with open(project_path_csv) as f:
        pairs = [
            {k: str(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)
        ]

    for pair in pairs:
        if isinstance(pair["label"], str):
            pair["label"] = float(pair["label"])

    train_pairs = []
    for pair in pairs:
        train_pairs.append(
            InputExample(texts=[pair["text1"], pair["text2"]], label=pair["label"])
        )

    train_dataloader = DataLoader(train_pairs, shuffle=True, batch_size=16)
    train_loss = losses.CosineSimilarityLoss(models.default)

    models.default.fit(
        train_objectives=[(train_dataloader, train_loss)], epochs=1, warmup_steps=100
    )

    project_path_model = paths.path_models(project)
    models.default.save(project_path_model)

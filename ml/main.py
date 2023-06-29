from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from typing import List

import files
import paths
import train as trainModule
import utils

app = FastAPI()


class Encode(BaseModel):
    text: List


@app.get("/encode/{project}")
async def encode(encode: Encode, project):
    return {"results": utils.encode(project, encode.text).tolist()}


class Train(BaseModel):
    file: UploadFile


@app.post("/train/{project}")
async def train(train: Train, project):
    files.write(paths.path_csv(train.file))
    trainModule.train(project)
    utils.reload()
    return {"status": "trained"}

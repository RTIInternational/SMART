from fastapi import FastAPI, File, UploadFile
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
def encode(encode: Encode, project):
    return {"results": utils.encode(project, encode.text).tolist()}


@app.post("/train/{project}")
def train(project, file: UploadFile = File(...)):
    files.write(paths.path_csv(project), file)
    trainModule.train(project)
    utils.reload()
    return {"status": "trained"}

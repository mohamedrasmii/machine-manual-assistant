#!/usr/bin/env python
# coding: utf-8

# In[2]:

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rag2 import ask_machine

app = FastAPI()


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/script.js")
def script():
    return FileResponse("script.js")


@app.post("/ask")
def ask_machine_api(request: QuestionRequest):
    return ask_machine(request.question)


# In[ ]:





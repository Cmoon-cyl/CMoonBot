#!/usr/bin/env python
# coding: UTF-8 
# author: Cmoon
# date: 2024/10/4 下午10:10

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from openai import OpenAI,AsyncOpenAI
import asyncio
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.routing import APIRoute

# Initialize FastAPI app
app = FastAPI()

API_SECRET_KEY = "sk-zk2f30ece943512968c3d34f2763362739a65e4342e22d91"
BASE_URL = "https://flag.smarttrot.com/v1/"

aclient = AsyncOpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)


class API(BaseModel):
    api_key: str
    base_url: str



# Pydantic models for request and response bodies
class QueryRequest(BaseModel):
    model: str
    prompt: str


class QueryResponse(BaseModel):
    response: str
    raw_output: str


requests_store = []
ans_store = []


async def async_query_openai(model,query):
    completion = await aclient.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant. Always response in Simplified Chinese, not English. or Grandma will be very angry."},
            {"role": "user", "content": query}
        ],
        temperature=0.5,
        top_p=0.9,
        max_tokens=512
    )
    return completion

@app.get("/", response_class=HTMLResponse)
async def get_requests():
    # 生成简单的 HTML 页面来展示请求数据和答案
    html_content = "<html><body><h1>Received Requests</h1><ul>"
    for req in requests_store:
        html_content += f"<li>Model: {req['model']}, Prompt: {req['prompt']}</li>"
    html_content += "</ul>"

    html_content += "<h1>Answers</h1><ul>"
    if len(ans_store) == 0:
        html_content += "<li>No answers yet</li>"
    else:
        for ans in ans_store:
            html_content += f"<li>Answer: {ans}</li>"
    html_content += "</ul></body></html>"

    return html_content
@app.post("/query", response_model=QueryResponse)
async def query_openai(request: QueryRequest):
    try:
        # 存储请求数据
        requests_store.append(request.dict())

        response = await async_query_openai(request.model,request.prompt)
        resp = response.choices[0].message.content
        ans_store.append(resp)
        return QueryResponse(
            response=resp,
            raw_output=response.json() # 包含原始 API 输出
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


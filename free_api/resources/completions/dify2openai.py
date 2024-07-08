#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : dify2openai
# @Time         : 2024/6/20 08:49
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import os
import random
import string
from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import httpx
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

if not os.getenv("DIFY_API_URL"):
    raise ValueError("DIFY API URL is required.")


def generate_id():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(29))


bot_type = os.getenv("BOT_TYPE", 'Chat')
input_variable = os.getenv("INPUT_VARIABLE", '')
output_variable = os.getenv("OUTPUT_VARIABLE", '')

api_path = {
    'Chat': '/chat-messages',
    'Completion': '/completion-messages',
    'Workflow': '/workflows/run'
}.get(bot_type)

if api_path is None:
    raise ValueError('Invalid bot type in the environment variable.')


@router.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head>
        <title>DIFY2OPENAI</title>
      </head>
      <body>
        <h1>Dify2OpenAI</h1>
        <p>Congratulations! Your project has been successfully deployed.</p>
      </body>
    </html>
    """


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized.")

    token = auth_header.split(" ")[1]
    data = await request.json()
    messages = data.get("messages", [])

    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    if bot_type == 'Chat':
        last_message = messages[-1]
        query_string = f"here is our talk history:\n'''\n" + \
                       "\n".join([f"{m['role']}: {m['content']}" for m in messages[:-1]]) + \
                       f"\n'''\n\nhere is my question:\n{last_message['content']}"
    else:
        query_string = messages[-1]['content']

    stream = data.get("stream", False)
    request_body = {
        "inputs": {input_variable: query_string} if input_variable else {},
        "query": query_string,
        "response_mode": "streaming",
        "conversation_id": "",
        "user": "apiuser",
        "auto_generate_name": False
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            os.getenv("DIFY_API_URL") + api_path,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json=request_body
        )
        resp.raise_for_status()

        if stream:
            return StreamingResponse(
                content=stream_response(resp, data),
                media_type="text/event-stream"
            )
        else:
            return await handle_non_streaming_response(resp, data)


async def stream_response(resp, data):
    buffer = ""
    is_first_chunk = True
    async for chunk in resp.aiter_text():
        buffer += chunk
        lines = buffer.split("\n")
        for line in lines[:-1]:
            if line.startswith("data:"):
                line = line[5:].strip()
                try:
                    chunk_obj = json.loads(line)
                    if chunk_obj.get("event") in ["message", "agent_message"]:
                        chunk_content = chunk_obj.get("answer", "").strip()
                        if is_first_chunk:
                            chunk_content = chunk_content.lstrip()
                            is_first_chunk = False
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk_content}}]})}\n\n"
                    elif chunk_obj.get("event") == "workflow_finished":
                        output_data = chunk_obj["data"]["outputs"]
                        output_content = output_data.get(output_variable, output_data)
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': output_content}}]})}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    elif chunk_obj.get("event") == "message_end":
                        yield "data: [DONE]\n\n"
                        return
                except json.JSONDecodeError:
                    pass
        buffer = lines[-1]


async def handle_non_streaming_response(resp, data):
    result = ""
    usage_data = ""
    message_ended = False
    buffer = ""
    async for chunk in resp.aiter_text():
        buffer += chunk
        lines = buffer.split("\n")
        for line in lines[:-1]:
            if line.startswith("data:"):
                line = line[5:].strip()
                try:
                    chunk_obj = json.loads(line)
                    if chunk_obj.get("event") in ["message", "agent_message"]:
                        result += chunk_obj.get("answer", "")
                    elif chunk_obj.get("event") == "message_end":
                        message_ended = True
                        usage_data = {
                            "prompt_tokens": chunk_obj["metadata"]["usage"].get("prompt_tokens", 100),
                            "completion_tokens": chunk_obj["metadata"]["usage"].get("completion_tokens", 10),
                            "total_tokens": chunk_obj["metadata"]["usage"].get("total_tokens", 110),
                        }
                except json.JSONDecodeError:
                    pass
        buffer = lines[-1]

    if message_ended:
        formatted_response = {
            "id": f"chatcmpl-{generate_id()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data["model"],
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.strip(),
                },
                "finish_reason": "stop",
            }],
            "usage": usage_data,
            "system_fingerprint": "fp_2f57f81c11",
        }
        return JSONResponse(formatted_response)
    else:
        raise HTTPException(status_code=500, detail="Unexpected end of stream.")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : polling_openai_api_keys
# @Time         : 2024/6/17 17:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from meutils.decorators.contextmanagers import atry_catch

from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.llm.openai_polling.chat import Completions
from meutils.llm.openai_polling.images import Images

from meutils.schemas.openai_types import CompletionRequest
from meutils.schemas.image_types import ImageRequest, ImagesResponse

from meutils.serving.fastapi.dependencies import get_headers, get_bearer_token

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["轮询"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]

"""
1. 多账号轮询
2. redis/string
3. 自动剔除账号
4. 支持任意任务：不仅仅是chat
5. 支持重定向
6. 支持流转非流、非流转流
7. 计算tokens

“{model}::{redirect_model}”
"""


@router.post("/chat/{path:path}")
async def create_chat_completions(
        path: str,  # "chat/completions"

        request: CompletionRequest,

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

        request_model: Optional[str] = Query(None),  # 优先级最高
        response_model: Optional[str] = Query(None),  # 兼容newapi自定义接口 ?response_model=""

        thinking: Optional[str] = Query(None),

):
    # logger.debug(request.model_dump_json(exclude_none=True, indent=4))

    # headers 代理
    http_client = None
    if proxy := headers.get("x-proxy"):
        proxy = random.choice(proxy.split(",") + [None])
        http_client = httpx.AsyncClient(proxy=proxy, timeout=100)

    # https://all.chatfire.cc/g/openai
    base_url = headers.get("base-url") or headers.get("x-base-url") or "https://api.siliconflow.cn/v1"  # newapi里需反代

    response_model = response_model or request.model
    async with atry_catch(f"{base_url}/{path}", api_key=api_key, headers=headers, request=request):
        ###########################################################################
        # 重定向：deepseek-chat==deepseek-v3 展示key 调用value

        if request_model:
            request.model = request_model

        if "==" in request.model:
            response_model, request_model = request.model.split("==", maxsplit=1)
            request.model = request_model

        ###########################################################################

        if thinking:
            if request.model.startswith('doubao'):
                request.thinking = {"type": thinking}  # disabled enabled auto

        client = Completions(base_url=base_url, api_key=api_key, http_client=http_client)
        response = await client.create(request)

        # exceeds the maximum
        # System is too busy now. Please try again later.
        # 400 {"code":20015,"message":"length of prompt_tokens (235121) must be less than max_seq_len (65536).","data":null}

        if request.stream:
            return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=response_model))

        if hasattr(response, "model"):
            response.model = response_model

        return response


@router.post("/images/{path:path}")
async def create_images_generations(
        path: str,  # "images/generations" ############ todo 兼容 chat
        request: ImageRequest,

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

        response_model: Optional[str] = Query(None),  # 兼容newapi自定义接口 ?model=""

):
    # headers 代理
    http_client = None
    if proxy := headers.get("x-proxy"):
        proxy = random.choice(proxy.split(",") + [None])
        http_client = httpx.AsyncClient(proxy=proxy, timeout=100)

    base_url = headers.get("base-url") or headers.get("x-base-url") or "https://api.siliconflow.cn/v1"

    response_model = response_model or request.model
    async with atry_catch(f"{base_url}/{path}", api_key=api_key, headers=headers, request=request):
        ###########################################################################
        # 重定向：deepseek-chat==deepseek-v3 展示key 调用value

        if "==" in request.model:
            response_model, request_model = request.model.split("==", maxsplit=1)
            request.model = request_model

        ###########################################################################

        images = Images(base_url=base_url, api_key=api_key, http_client=http_client)
        response = await images.generate(request)

        if hasattr(response, "model"):
            response.model = response_model

        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

"""

{
    "base_url": "https://all.chatfire.cc/g/openai"
}


curl -X 'POST' \
  'http://0.0.0.0:8000/v1/xx' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer redis:https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=rWMtht' \
  -H 'base_url: https://all.chatfire.cc/g/openai' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "xxxxxxxx:gemini-2.0-flash",
  "stream": true
}'

curl -X 'POST' \
  'https://all.chatfire.cn/polling/v1/x' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer redis:https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=kfKGzt' \
  -H 'base-url: https://all.chatfire.cc/g/openai' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "gemini-2.0-flash",
  "stream": true
}'

curl -X 'POST' \
  'https://openai-dev.chatfire.cn/polling_plus/v1/x' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer redis:https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=kfKGzt' \
  -H 'base_url: https://all.chatfire.cc/g/openai' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "gemini-2.0-flash",
  "stream": true
}'


curl -X 'POST' \
  'https://openai-dev.chatfire.cn/polling_plus/v1/x' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer AIzaSyAcVutR1bYxUq8M9hqw4870t2W9zFthKkY' \
  -H 'base_url: https://all.chatfire.cc/g/openai' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "gemini-2.0-flash",
  "stream": true
}'

curl -X 'POST' \
  'http://0.0.0.0:8000/v1/xx' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer redis:https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=xlvlrH' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
  "stream": true
}'

curl -X 'POST' \
  'http://0.0.0.0:8000/v1/xx' \
  -H 'accept: application/json' \
  -H 'x-base-url: https://all.chatfire.cc/g/openai' \
  -H 'Authorization: Bearer AIzaSyAcVutR1bYxUq8M9hqw4870t2W9zFthKkY' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "gemini-2.0-flash",
  "stream": true
}'

curl -X 'POST' \
  'http://0.0.0.0:8000/polling_plus/v1/xx' \
  -H 'accept: application/json' \
  -H 'base_url: https://all.chatfire.cc/g/openai' \
  -H 'Authorization: Bearer AIzaSyAcVutR1bYxUq8M9hqw4870t2W9zFthKkY' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "gemini-2.0-flash",
  "stream": false
}'

"""

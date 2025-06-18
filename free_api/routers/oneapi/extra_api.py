#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : extra_api
# @Time         : 2024/9/18 13:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.notice.feishu import send_message

from meutils.llm.openai_utils import create_chat_completion_chunk

from meutils.schemas.openai_types import CompletionRequest, chat_completion, chat_completion_chunk, \
    chat_completion_chunk_stop

from meutils.schemas.image_types import ImageRequest, ImagesResponse

from meutils.apis.oneapi.user import get_user, get_api_key_log
from meutils.apis.oneapi.channel import ChannelInfo, create_or_update_channel

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["oneapi"]


@router.get("/token")
async def get_user_info(
        api_key: Optional[str] = Depends(get_bearer_token),
):
    data = await get_api_key_log(api_key)
    if data and (user_id := data[0]['user_id']):
        if data := await get_user(user_id):
            data['data']['access_token'] = '🔥chatfire'
            return data


@router.post("/channel")
async def create_channel(
        request: ChannelInfo,
        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),
):
    upstream_base_url = headers.get('upstream-base-url')
    upstream_api_key = headers.get('upstream-api-key')

    # 渠道选择
    request.key = api_key  # 1000以内

    if "volc" in request.base_url:  # 火山渠道
        from meutils.apis.volcengine_apis.videos import get_valid_token

        token = await get_valid_token()
        request.key = token

    response = await create_or_update_channel(request, upstream_base_url, upstream_api_key)
    response['request'] = request
    return response


@router.post("/billing/v1/{dynamic_router:path}")  # 动态计费
async def chat_completions(
        dynamic_router: str,  # chat/completions

        request: dict,

):
    if "chat/completions" in dynamic_router:
        request = CompletionRequest(**request)

        if request.stream:
            chat_completion_chunk.usage = request.usage

            def gen():

                yield chat_completion_chunk
                yield chat_completion_chunk_stop.model_dump_json()
                yield "[DONE]"  # 兼容标准格式

            return EventSourceResponse(gen())
        else:
            chat_completion.usage = request.usage

            return chat_completion


    elif "images/generations" in dynamic_router:
        request = ImageRequest(**request)

        return ImagesResponse(usage=request.usage)


"""
UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=


curl -X 'POST' 'http://openai-dev.chatfire.cn/oneapi/channel' \
    -H 'Authorization: Bearer xx' \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "name": "火山",
        "tag": "火山",
        "key": "$KEY",
        "type": 8,
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        
        "models": "doubao-seed-1-6-250615,doubao-seed-1-6-flash-250615,doubao-seed-1-6-thinking-250615,doubao-1-5-ui-tars-250428,deepseek-r1-250528,doubao-1-5-thinking-pro-m-250428,doubao-1-5-thinking-vision-pro-250428,doubao-1.5-vision-pro-250328,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324,deepseek-v3-8k,deepseek-v3-128k,deepseek-chat,deepseek-chat-8k,deepseek-chat-64k,deepseek-chat-164k,deepseek-chat:function,deepseek-vl2,deepseek-ai/deepseek-vl2,deepseek-r1,deepseek-r1-8k,deepseek-reasoner,deepseek-reasoner-8k,deepseek-r1-250120,deepseek-search,deepseek-r1-search,deepseek-reasoner-search,deepseek-r1-think,deepseek-reasoner-think,deepseek-r1-plus,deepseek-r1:1.5b,deepseek-r1-lite,deepseek-r1-distill-qwen-1.5b,deepseek-r1:7b,deepseek-r1-distill-qwen-7b,deepseek-r1:8b,deepseek-r1-distill-llama-8b,deepseek-r1:14b,deepseek-r1-distill-qwen-14b,deepseek-r1:32b,deepseek-r1-distill-qwen-32b,deepseek-r1:70b,deepseek-r1-distill-llama-70b,deepseek-r1-metasearch,doubao-1-5-pro-32k,doubao-1-5-pro-32k-250115,doubao-1-5-pro-256k,doubao-1-5-pro-256k-250115,doubao-1-5-vision-pro-32k,doubao-1-5-vision-pro-32k-250115,doubao-lite-128k,doubao-lite-32k,doubao-lite-32k-character,doubao-lite-4k,doubao-1.5-lite-32k,doubao-pro-4k,doubao-pro-32k,doubao-pro-32k-character,doubao-pro-128k,doubao-pro-256k,doubao-1.5-pro-32k,doubao-1.5-pro-256k,doubao-1.5-vision-pro-32k,doubao-vision-lite-32k,doubao-vision-pro-32k,doubao-1-5-pro-thinking,doubao-1-5-vision-thinking,doubao-1-5-thinking-pro-250415,doubao-1-5-thinking-pro-vision,doubao-1-5-thinking-pro-vision-250415,doubao-1-5-thinking-pro-m-250415,moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k",
        "group": "default,deepseek,volcengine",
        "model_mapping": "{\n  \"deepseek-r1\": \"deepseek-r1-250120\",\n  \"deepseek-reasoner\": \"deepseek-r1-250120\",\n  \"deepseek-v3-0324\": \"deepseek-v3-250324\",\n  \"deepseek-v3\": \"deepseek-v3-250324\",\n  \"deepseek-chat\": \"deepseek-v3-250324\",\n  \"doubao-1-5-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-1.5-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-pro-32k\": \"doubao-1-5-pro-32k-250115\",\n  \"doubao-pro-256k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1.5-lite-32k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-4k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-32k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-128k\": \"doubao-lite-128k-240828\",\n  \"doubao-pro-128k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1.5-lite\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-vision-lite-32k\": \"doubao-vision-lite-32k-241015\",\n  \"doubao-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-1.5-pro-32k\": \"doubao-1-5-pro-32k-250115\",\n  \"doubao-1.5-pro-256k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1-5-thinking-pro\": \"doubao-1-5-thinking-pro-250415\",\n  \"doubao-1-5-thinking-pro-vision\": \"doubao-1-5-thinking-pro-vision-250415\"\n}"
    }'


UPSTREAM_BASE_URL=http://38.147.104.170:3007
UPSTREAM_API_KEY=LtxK4J6YOjdHOpXqwfiHE7BoWyeWNpXH


curl -X 'POST' 'http://openai-dev.chatfire.cn/oneapi/channel' \
    -H 'Authorization: Bearer xx' \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id":2,
        "name": "火山",
        "tag": "火山",
        "key": "$KEY",
        "type": 8,
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        
        "models": "doubao-seed-1-6-250615,doubao-seed-1-6-flash-250615,doubao-seed-1-6-thinking-250615,doubao-1-5-ui-tars-250428,deepseek-r1-250528,doubao-1-5-thinking-pro-m-250428,doubao-1-5-thinking-vision-pro-250428,doubao-1.5-vision-pro-250328,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324,deepseek-v3-8k,deepseek-v3-128k,deepseek-chat,deepseek-chat-8k,deepseek-chat-64k,deepseek-chat-164k,deepseek-chat:function,deepseek-vl2,deepseek-ai/deepseek-vl2,deepseek-r1,deepseek-r1-8k,deepseek-reasoner,deepseek-reasoner-8k,deepseek-r1-250120,deepseek-search,deepseek-r1-search,deepseek-reasoner-search,deepseek-r1-think,deepseek-reasoner-think,deepseek-r1-plus,deepseek-r1:1.5b,deepseek-r1-lite,deepseek-r1-distill-qwen-1.5b,deepseek-r1:7b,deepseek-r1-distill-qwen-7b,deepseek-r1:8b,deepseek-r1-distill-llama-8b,deepseek-r1:14b,deepseek-r1-distill-qwen-14b,deepseek-r1:32b,deepseek-r1-distill-qwen-32b,deepseek-r1:70b,deepseek-r1-distill-llama-70b,deepseek-r1-metasearch,doubao-1-5-pro-32k,doubao-1-5-pro-32k-250115,doubao-1-5-pro-256k,doubao-1-5-pro-256k-250115,doubao-1-5-vision-pro-32k,doubao-1-5-vision-pro-32k-250115,doubao-lite-128k,doubao-lite-32k,doubao-lite-32k-character,doubao-lite-4k,doubao-1.5-lite-32k,doubao-pro-4k,doubao-pro-32k,doubao-pro-32k-character,doubao-pro-128k,doubao-pro-256k,doubao-1.5-pro-32k,doubao-1.5-pro-256k,doubao-1.5-vision-pro-32k,doubao-vision-lite-32k,doubao-vision-pro-32k,doubao-1-5-pro-thinking,doubao-1-5-vision-thinking,doubao-1-5-thinking-pro-250415,doubao-1-5-thinking-pro-vision,doubao-1-5-thinking-pro-vision-250415,doubao-1-5-thinking-pro-m-250415,moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k",
        "group": "default,deepseek,volcengine",
        "model_mapping": "{\n  \"deepseek-r1\": \"deepseek-r1-250120\",\n  \"deepseek-reasoner\": \"deepseek-r1-250120\",\n  \"deepseek-v3-0324\": \"deepseek-v3-250324\",\n  \"deepseek-v3\": \"deepseek-v3-250324\",\n  \"deepseek-chat\": \"deepseek-v3-250324\",\n  \"doubao-1-5-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-1.5-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-pro-32k\": \"doubao-1-5-pro-32k-250115\",\n  \"doubao-pro-256k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1.5-lite-32k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-4k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-32k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-128k\": \"doubao-lite-128k-240828\",\n  \"doubao-pro-128k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1.5-lite\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-vision-lite-32k\": \"doubao-vision-lite-32k-241015\",\n  \"doubao-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-1.5-pro-32k\": \"doubao-1-5-pro-32k-250115\",\n  \"doubao-1.5-pro-256k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1-5-thinking-pro\": \"doubao-1-5-thinking-pro-250415\",\n  \"doubao-1-5-thinking-pro-vision\": \"doubao-1-5-thinking-pro-vision-250415\"\n}"
    }'
"""

if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

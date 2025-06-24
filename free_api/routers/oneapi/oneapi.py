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

from meutils.apis.oneapi.user import get_user, get_api_key_log
from meutils.apis.oneapi.channel import ChannelInfo, create_or_update_channel as _create_or_update_channel

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

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

    logger.debug(upstream_base_url)
    logger.debug(upstream_api_key)
    logger.debug(api_key)
    logger.debug(request.base_url)

    create_or_update_channel = partial(
        _create_or_update_channel,
        base_url=upstream_base_url,
        api_key=upstream_api_key
    )

    # 飞书表格全部 key
    request.key = api_key

    ############################################### 业务定制
    if "volc" in request.base_url:  # 火山渠道
        from meutils.apis.volcengine_apis.videos import get_valid_token

        tokens = api_key and api_key.split()  # null

        request.key = await get_valid_token(tokens)

    ###############################################

    response = await create_or_update_channel(request)
    if isinstance(response, list):
        response = response[-1]

    response['request'] = request
    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/oneapi')

    app.run()

"""
UPSTREAM_BASE_URL=https://api.chatfire.cn
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/GYCHsvI4qhnDPNtI4VPcdw2knEd?sheet=Gvm9dt[:20]
BASE_URL=https://openai.chatfire.cn/images


curl -X 'POST' 'http://0.0.0.0:8000/oneapi/channel' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "10010:10030",
        "name": "fal-flux",
        "tag": "fal-flux",
        "key": "$KEY",
        "type": 1,
        "priority": 888,

        "base_url": "'$BASE_URL'",
        "group": "default",

        "models":  "imagen4,recraft-v3,recraftv3,flux-pro-1.1-ultra,flux-kontext-pro,flux-kontext-max",
        "model_mapping": {
          "flux-pro-1.1-ultra": "fal-ai/flux-pro/v1.1-ultra",
          "ideogram-ai/ideogram-v2-turbo": "fal-ai/ideogram/v2/turbo",
          "ideogram-ai/ideogram-v2": "fal-ai/ideogram/v2",
          "recraftv3": "fal-ai/recraft-v3",
          "recraft-v3": "fal-ai/recraft-v3",
          "imagen4": "fal-ai/imagen4/preview",
          "flux-kontext-pro": "fal-ai/flux-pro/kontext",
          "flux-kontext-max": "fal-ai/flux-pro/kontext/max"
        }
    }'
    
UPSTREAM_BASE_URL=https://api.chatfire.cn
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/GYCHsvI4qhnDPNtI4VPcdw2knEd?sheet=LGVKwN[:10]
BASE_URL=https://api-singapore.klingai.com


curl -X 'POST' 'http://0.0.0.0:8000/oneapi/channel' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "10000:10010",
        "name": "可灵视频",
        "tag": "可灵视频",
        "key": "$KEY",
        "type": 104,
        "priority": 0,

        "base_url": "'$BASE_URL'",
        "group": "default",

        "models":  "kling_video,kling_extend,kling_effects,kling_lip_sync"
    }'

UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/MekfsfVuohfUf1tsWV0cCvTmn3c?sheet=305f17[:1000]
BASE_URL=https://api-inference.modelscope.cn


curl -X 'POST' 'http://0.0.0.0:8000/oneapi/channel' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id":"",
        "name": "modelscope",
        "tag": "modelscope",
        "key": "$KEY",
        "type": 0,
        "priority": 666,

        "base_url": "'$BASE_URL'",
        "group": "default,deepseek",

        "models": "deepseek-r1,deepseek-r1-0528,deepseek-r1-250528,deepseek-chat,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324",
        "model_mapping": {
            "deepseek-reasoner": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1-0528": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1-250528": "deepseek-ai/DeepSeek-R1-0528",
        
            "deepseek-chat": "deepseek-ai/DeepSeek-V3",
            "deepseek-v3": "deepseek-ai/DeepSeek-V3",
            "deepseek-v3-0324": "deepseek-ai/DeepSeek-V3-0324",
            "deepseek-v3-250324": "deepseek-ai/DeepSeek-V3-0324",
        
            "majicflus_v1": "MAILAND/majicflus_v1"
        } 

    }'

UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=ICzCsC[:1000]
BASE_URL=https://all.chatfire.cn/ppinfra/v1/chat/completions

curl -X 'POST' 'http://0.0.0.0:8000/oneapi/channel' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id":"",
        "name": "ppinfra",
        "tag": "ppinfra",
        "key": "$KEY",
        "type": 8,
        "priority": 888,

        "base_url": "'$BASE_URL'",
        "group": "default,deepseek",

        "models": "deepseek-r1,deepseek-r1-0528,deepseek-r1-250528,deepseek-chat,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324",
        "model_mapping": {
            "deepseek-prover-v2-671b": "deepseek/deepseek-prover-v2-671b",

            "deepseek-chat": "deepseek/deepseek-v3-0324",
            "deepseek-v3": "deepseek/deepseek-v3-0324",
            "deepseek-v3-0324": "deepseek/deepseek-v3-0324",
            "deepseek-v3-250324": "deepseek/deepseek-v3-0324",

            "deepseek-r1": "deepseek/deepseek-r1-0528",
            "deepseek-r1-0528": "deepseek/deepseek-r1-0528",
            "deepseek-r1-250528": "deepseek/deepseek-r1-0528",

            "deepseek-reasoner": "deepseek/deepseek-r1-0528"
        }  

    }'




UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=


curl -X 'POST' 'http://openai-dev.chatfire.cn/oneapi/channel' \
    -H 'Authorization: Bearer null' \
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

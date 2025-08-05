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

from meutils.apis.oneapi.tasks import polling_tasks, refund_tasks
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


@router.get("/tasks/{type}")
async def get_tasks(
        type: str = "polling",
        # api_key: Optional[str] = Depends(get_bearer_token),
):
    if type == "polling":
        return await polling_tasks()
    elif type == "refund":
        return await refund_tasks()


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

    ############################################### 业务定制 超刷
    if "volc" in request.base_url and str(request.id) == "21222":  # 火山渠道 超刷
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
UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=ICzCsC[:100]
BASE_URL=https://api.ppinfra.com/v3/openai/chat/completions


curl -X 'POST' http://0.0.0.0:8000/oneapi/channel \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "1:100",

        "name": "ppio",
        "tag": "ppio",
        "key": "$KEY",
        "type": 8,

        "base_url": "'$BASE_URL'",
        "group": "default,china",

        "models": "kimi-k2-0711-preview,moonshotai/kimi-k2-instruct",
        "model_mapping": {
            "kimi-k2-0711-preview": "moonshotai/kimi-k2-instruct"
        } 

    }'


UPSTREAM_BASE_URL=https://api.chatfire.cn
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/GYCHsvI4qhnDPNtI4VPcdw2knEd?sheet=Gvm9dt[:30]
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


curl -X 'POST' http://0.0.0.0:8000/oneapi/channel \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "2000:3000",

        "name": "modelscope",
        "tag": "modelscope",
        "key": "$KEY",
        "type": 1,

        "base_url": "'$BASE_URL'",
        "group": "default,deepseek",

        "models": "qwen3-coder-480b-a35b-instruct,qwen3-235b-a22b-instruct-2507,qwen3-235b-a22b-thinking-2507,qwen3-30b-a3b-instruct-2507,kimi-k2-0711-preview,moonshotai/kimi-k2-instruct,glm-4.5,deepseek-r1,deepseek-r1-0528,deepseek-r1-250528,deepseek-chat,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324,PaddlePaddle/ERNIE-4.5-21B-A3B-PT,PaddlePaddle/ERNIE-4.5-0.3B-PT,PaddlePaddle/ERNIE-4.5-VL-28B-A3B-PT,PaddlePaddle/ERNIE-4.5-300B-A47B-PT,qwen2.5-coder-32b-instruct,qwen2.5-coder-14b-instruct,qwen2.5-coder-7b-instruct,qwen2.5-72b-instruct,qwen2.5-32b-instruct,qwen2.5-14b-instruct,qwen2.5-7b-instruct,qwq-32b-preview,qvq-72b-preview,qwen2-vl-7b-instruct,qwen2.5-14b-instruct-1m,qwen2.5-7b-instruct-1m,qwen2.5-vl-3b-instruct,qwen2.5-vl-7b-instruct,qwen2.5-vl-72b-instruct,qwq-32b,qwen2.5-vl-32b-instruct,qwen3-0.6b,qwen3-1.7b,qwen3-4b,qwen3-8b,qwen3-14b,qwen3-30b-a3b,qwen3-32b,qwen3-235b-a22b",
        "model_mapping": {
            "deepseek-reasoner": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1-0528": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1-250528": "deepseek-ai/DeepSeek-R1-0528",
        
            "deepseek-chat": "deepseek-ai/DeepSeek-V3",
            "deepseek-v3": "deepseek-ai/DeepSeek-V3",
            "deepseek-v3-0324": "deepseek-ai/DeepSeek-V3-0324",
            "deepseek-v3-250324": "deepseek-ai/DeepSeek-V3-0324",
        
            "majicflus_v1": "MAILAND/majicflus_v1",
            "flux-kontext-dev": "black-forest-labs/FLUX.1-Kontext-dev",
            
            "qwen2.5-coder-32b-instruct": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "qwen2.5-coder-14b-instruct": "Qwen/Qwen2.5-Coder-14B-Instruct",
            "qwen2.5-coder-7b-instruct": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "qwen2.5-72b-instruct": "Qwen/Qwen2.5-72B-Instruct",
            "qwen2.5-32b-instruct": "Qwen/Qwen2.5-32B-Instruct",
            "qwen2.5-14b-instruct": "Qwen/Qwen2.5-14B-Instruct",
            "qwen2.5-7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
            "qwq-32b-preview": "Qwen/QwQ-32B-Preview",
            "qvq-72b-preview": "Qwen/QVQ-72B-Preview",
            "qwen2-vl-7b-instruct": "Qwen/Qwen2-VL-7B-Instruct",
            "qwen2.5-14b-instruct-1m": "Qwen/Qwen2.5-14B-Instruct-1M",
            "qwen2.5-7b-instruct-1m": "Qwen/Qwen2.5-7B-Instruct-1M",
            "qwen2.5-vl-3b-instruct": "Qwen/Qwen2.5-VL-3B-Instruct",
            "qwen2.5-vl-7b-instruct": "Qwen/Qwen2.5-VL-7B-Instruct",
            "qwen2.5-vl-72b-instruct": "Qwen/Qwen2.5-VL-72B-Instruct",
            "qwq-32b": "Qwen/QwQ-32B",
            "qwen2.5-vl-32b-instruct": "Qwen/Qwen2.5-VL-32B-Instruct",
            "qwen3-0.6b": "Qwen/Qwen3-0.6B",
            "qwen3-1.7b": "Qwen/Qwen3-1.7B",
            "qwen3-4b": "Qwen/Qwen3-4B",
            "qwen3-8b": "Qwen/Qwen3-8B",
            "qwen3-14b": "Qwen/Qwen3-14B",
            "qwen3-30b-a3b": "Qwen/Qwen3-30B-A3B",
            "qwen3-32b": "Qwen/Qwen3-32B",
            "qwen3-235b-a22b": "Qwen/Qwen3-235B-A22B",
            "qwen3-coder-480b-a35b-instruct": "Qwen/Qwen3-Coder-480B-A35B-Instruct",
            "qwen3-235b-a22b-instruct-2507": "Qwen/Qwen3-235B-A22B-Instruct-2507",
            "qwen3-235b-a22b-thinking-2507": "Qwen/Qwen3-235B-A22B-Thinking-2507",
            "qwen3-30b-a3b-instruct-2507": "Qwen/Qwen3-30B-A3B-Instruct-2507",

            "glm-4.5": "ZhipuAI/GLM-4.5",
            "kimi-k2-0711-preview": "moonshotai/Kimi-K2-Instruct",
            "moonshotai/kimi-k2-instruct": "moonshotai/Kimi-K2-Instruct"

        },
        
        "status_code_mapping": "{\n  \"429\": \"500\"\n}"

    }'
    
    



UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=ICzCsC[:100]
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
        "id":2,
        "name": "火山",
        "tag": "火山",
        "key": "$KEY",
        "type": 8,
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",

        "models": "doubao-seed-1-6-250615,doubao-seed-1-6-flash-250615,doubao-seed-1-6-thinking-250615,doubao-1-5-ui-tars-250428,deepseek-r1-250528,doubao-1-5-thinking-pro-m-250428,doubao-1-5-thinking-vision-pro-250428,doubao-1.5-vision-pro-250328,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324,deepseek-v3-8k,deepseek-v3-128k,deepseek-chat,deepseek-chat-8k,deepseek-chat-64k,deepseek-chat-164k,deepseek-chat:function,deepseek-vl2,deepseek-ai/deepseek-vl2,deepseek-r1,deepseek-r1-8k,deepseek-reasoner,deepseek-reasoner-8k,deepseek-r1-250120,deepseek-search,deepseek-r1-search,deepseek-reasoner-search,deepseek-r1-think,deepseek-reasoner-think,deepseek-r1-plus,deepseek-r1:1.5b,deepseek-r1-lite,deepseek-r1-distill-qwen-1.5b,deepseek-r1:7b,deepseek-r1-distill-qwen-7b,deepseek-r1:8b,deepseek-r1-distill-llama-8b,deepseek-r1:14b,deepseek-r1-distill-qwen-14b,deepseek-r1:32b,deepseek-r1-distill-qwen-32b,deepseek-r1:70b,deepseek-r1-distill-llama-70b,deepseek-r1-metasearch,doubao-1-5-pro-32k,doubao-1-5-pro-32k-250115,doubao-1-5-pro-256k,doubao-1-5-pro-256k-250115,doubao-1-5-vision-pro-32k,doubao-1-5-vision-pro-32k-250115,doubao-lite-128k,doubao-lite-32k,doubao-lite-32k-character,doubao-lite-4k,doubao-1.5-lite-32k,doubao-pro-4k,doubao-pro-32k,doubao-pro-32k-character,doubao-pro-128k,doubao-pro-256k,doubao-1.5-pro-32k,doubao-1.5-pro-256k,doubao-1.5-vision-pro-32k,doubao-vision-lite-32k,doubao-vision-pro-32k,doubao-1-5-pro-thinking,doubao-1-5-vision-thinking,doubao-1-5-thinking-pro-250415,doubao-1-5-thinking-pro-vision,doubao-1-5-thinking-pro-vision-250415,doubao-1-5-thinking-pro-m-250415,moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k",
        "group": "default,deepseek,volc,volcengine",
        "model_mapping": "{\n  \"deepseek-r1\": \"deepseek-r1-250120\",\n  \"deepseek-reasoner\": \"deepseek-r1-250120\",\n  \"deepseek-v3-0324\": \"deepseek-v3-250324\",\n  \"deepseek-v3\": \"deepseek-v3-250324\",\n  \"deepseek-chat\": \"deepseek-v3-250324\",\n  \"doubao-1-5-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-1.5-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-pro-32k\": \"doubao-1-5-pro-32k-250115\",\n  \"doubao-pro-256k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1.5-lite-32k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-4k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-32k\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-lite-128k\": \"doubao-lite-128k-240828\",\n  \"doubao-pro-128k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1.5-lite\": \"doubao-1-5-lite-32k-250115\",\n  \"doubao-vision-lite-32k\": \"doubao-vision-lite-32k-241015\",\n  \"doubao-vision-pro-32k\": \"doubao-1-5-vision-pro-32k-250115\",\n  \"doubao-1.5-pro-32k\": \"doubao-1-5-pro-32k-250115\",\n  \"doubao-1.5-pro-256k\": \"doubao-1-5-pro-256k-250115\",\n  \"doubao-1-5-thinking-pro\": \"doubao-1-5-thinking-pro-250415\",\n  \"doubao-1-5-thinking-pro-vision\": \"doubao-1-5-thinking-pro-vision-250415\"\n}"
    }'


API_KEY=https://xchatllm.feishu.cn/sheets/MekfsfVuohfUf1tsWV0cCvTmn3c?sheet=305f17
BASE_URL=https://api-inference.modelscope.cn


curl -X 'POST' http://openai-dev.chatfire.cn/oneapi/channel \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "10000:10010",
        "name": "modelscope",
        "tag": "modelscope",
        "key": "$KEY",
        "type": 0,

        "base_url": "'$BASE_URL'",
        "group": "default,deepseek",

        "models": "deepseek-r1,deepseek-r1-0528,deepseek-r1-250528,deepseek-chat,deepseek-v3,deepseek-v3-0324,deepseek-v3-250324,PaddlePaddle/ERNIE-4.5-21B-A3B-PT,PaddlePaddle/ERNIE-4.5-0.3B-PT,PaddlePaddle/ERNIE-4.5-VL-28B-A3B-PT,PaddlePaddle/ERNIE-4.5-300B-A47B-PT,qwen2.5-coder-32b-instruct,qwen2.5-coder-14b-instruct,qwen2.5-coder-7b-instruct,qwen2.5-72b-instruct,qwen2.5-32b-instruct,qwen2.5-14b-instruct,qwen2.5-7b-instruct,qwq-32b-preview,qvq-72b-preview,qwen2-vl-7b-instruct,qwen2.5-14b-instruct-1m,qwen2.5-7b-instruct-1m,qwen2.5-vl-3b-instruct,qwen2.5-vl-7b-instruct,qwen2.5-vl-72b-instruct,qwq-32b,qwen2.5-vl-32b-instruct,qwen3-0.6b,qwen3-1.7b,qwen3-4b,qwen3-8b,qwen3-14b,qwen3-30b-a3b,qwen3-32b,qwen3-235b-a22b",
        "model_mapping": {
            "deepseek-reasoner": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1-0528": "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-r1-250528": "deepseek-ai/DeepSeek-R1-0528",
        
            "deepseek-chat": "deepseek-ai/DeepSeek-V3",
            "deepseek-v3": "deepseek-ai/DeepSeek-V3",
            "deepseek-v3-0324": "deepseek-ai/DeepSeek-V3-0324",
            "deepseek-v3-250324": "deepseek-ai/DeepSeek-V3-0324",
        
            "majicflus_v1": "MAILAND/majicflus_v1",
            
            "qwen2.5-coder-32b-instruct": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "qwen2.5-coder-14b-instruct": "Qwen/Qwen2.5-Coder-14B-Instruct",
            "qwen2.5-coder-7b-instruct": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "qwen2.5-72b-instruct": "Qwen/Qwen2.5-72B-Instruct",
            "qwen2.5-32b-instruct": "Qwen/Qwen2.5-32B-Instruct",
            "qwen2.5-14b-instruct": "Qwen/Qwen2.5-14B-Instruct",
            "qwen2.5-7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
            "qwq-32b-preview": "Qwen/QwQ-32B-Preview",
            "qvq-72b-preview": "Qwen/QVQ-72B-Preview",
            "qwen2-vl-7b-instruct": "Qwen/Qwen2-VL-7B-Instruct",
            "qwen2.5-14b-instruct-1m": "Qwen/Qwen2.5-14B-Instruct-1M",
            "qwen2.5-7b-instruct-1m": "Qwen/Qwen2.5-7B-Instruct-1M",
            "qwen2.5-vl-3b-instruct": "Qwen/Qwen2.5-VL-3B-Instruct",
            "qwen2.5-vl-7b-instruct": "Qwen/Qwen2.5-VL-7B-Instruct",
            "qwen2.5-vl-72b-instruct": "Qwen/Qwen2.5-VL-72B-Instruct",
            "qwq-32b": "Qwen/QwQ-32B",
            "qwen2.5-vl-32b-instruct": "Qwen/Qwen2.5-VL-32B-Instruct",
            "qwen3-0.6b": "Qwen/Qwen3-0.6B",
            "qwen3-1.7b": "Qwen/Qwen3-1.7B",
            "qwen3-4b": "Qwen/Qwen3-4B",
            "qwen3-8b": "Qwen/Qwen3-8B",
            "qwen3-14b": "Qwen/Qwen3-14B",
            "qwen3-30b-a3b": "Qwen/Qwen3-30B-A3B",
            "qwen3-32b": "Qwen/Qwen3-32B",
            "qwen3-235b-a22b": "Qwen/Qwen3-235B-A22B"

        } 

    }'


UPSTREAM_BASE_URL=https://api.ffire.cc
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=1DCblQ[:200]
BASE_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions



curl -X 'POST' 'http://0.0.0.0:8000/oneapi/channel' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "10000:10300",
        "name": "火山企业",
        "tag": "火山企业",
        "key": "$KEY",
        "type": 8,
        "priority": 999,
        "weight": 100,

        "base_url": "'$BASE_URL'",

        "models": "doubao-lite-4k,doubao-1.5-lite,doubao-1-5-vision-pro-32k,doubao-1.5-pro-256k,doubao-pro-32k,doubao-pro-128k,doubao-pro-256k,deepseek-r1-250120,deepseek-r1-0528,deepseek-r1-250528,doubao-1-5-thinking-pro,doubao-1-5-thinking-pro-250415,doubao-1-5-thinking-pro-vision,doubao-1-5-thinking-vision-pro-250428,doubao-seed-1-6-thinking-250715,doubao-seed-1-6-flash-250715,doubao-seed-1-6-250615,doubao-1-5-pro-32k-250115,doubao-1.5-pro-32k,deepseek-r1-250528,deepseek-r1,deepseek-reasoner,deepseek-v3-0324,deepseek-v3-250324,deepseek-v3,deepseek-chat,doubao-1-5-ui-tars-250428,doubao-1.5-vision-pro-250328,doubao-1-5-pro-256k-250115,moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k",
        "group": "default,volc,volcengine",
        
        "status_code_mapping": "{\n  \"429\": \"500\",\n\"403\": \"500\"}",
        "model_mapping": {
        
        "deepseek-r1": "deepseek-r1-250120",
        "deepseek-reasoner": "deepseek-r1-250120",
        "deepseek-r1-0528": "deepseek-r1-250528",
        
        "deepseek-v3-0324": "deepseek-v3-250324",
        "deepseek-v3": "deepseek-v3-250324",
        "deepseek-chat": "deepseek-v3-250324",
        
        "doubao-1-5-vision-pro-32k": "doubao-1-5-vision-pro-32k-250115",
        "doubao-1.5-vision-pro-32k": "doubao-1-5-vision-pro-32k-250115",
        
        "doubao-pro-32k": "doubao-pro-32k-241215",
        "doubao-pro-128k": "doubao-1-5-pro-256k-250115",
        "doubao-pro-256k": "doubao-1-5-pro-256k-250115",
        
        "doubao-1.5-pro-32k": "doubao-1-5-pro-32k-250115",
        "doubao-1.5-pro-256k": "doubao-1-5-pro-256k-250115",
        
        "doubao-1.5-lite-32k": "doubao-1-5-lite-32k-250115",
        "doubao-lite-4k": "doubao-1-5-lite-32k-250115",
        "doubao-lite-32k": "doubao-1-5-lite-32k-250115",
        "doubao-lite-128k": "doubao-lite-128k-240828",
        "doubao-1.5-lite": "doubao-1-5-lite-32k-250115",
        "doubao-vision-lite-32k": "doubao-vision-lite-32k-241015",
        "doubao-vision-pro-32k": "doubao-1-5-vision-pro-32k-250115",

        "doubao-1-5-thinking-pro": "doubao-1-5-thinking-pro-250415",
        "doubao-1-5-thinking-pro-vision": "doubao-seed-1-6-thinking-250715",
        "doubao-1-5-thinking-vision-pro-250428": "doubao-seed-1-6-thinking-250715"

        }
    }'



UPSTREAM_BASE_URL=https://api.chatfire.cn
UPSTREAM_API_KEY=

API_KEY=https://xchatllm.feishu.cn/sheets/GYCHsvI4qhnDPNtI4VPcdw2knEd?sheet=Gvm9dt[:50]
BASE_URL=https://openai.chatfire.cn/images


curl -X 'POST' 'http://openai-dev.chatfire.cn/oneapi/channel' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM-BASE-URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
      -d '{
        "id": "10010:10050",
        "name": "fal-flux",
        "tag": "fal-flux",
        "key": "$KEY",
        "type": 1,
        "priority": 888,

        "base_url": "'$BASE_URL'",
        "group": "default",

        "models":  "imagen3,imagen3-fast,imagen4,imagen4-fast,imagen4-ultra,recraft-v3,recraftv3,flux-pro-1.1-ultra,flux-kontext-pro,flux-kontext-max",
        "model_mapping": {
            "imagen3": "fal-ai/imagen3",
            "imagen3-fast": "fal-ai/imagen3/fast",

            "imagen4": "fal-ai/imagen4/preview",
            "imagen4-fast": "fal-ai/imagen4/preview/fast",
            "imagen4-ultra": "fal-ai/imagen4/preview/ultra",
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


"""
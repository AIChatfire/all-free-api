#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : common
# @Time         : 2024/12/20 16:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 外置接口：计费
"""todo
1. hook 输出输出映射
2. 异步转chat
"""

from meutils.pipe import *

from meutils.db.redis_db import redis_aclient
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message
from meutils.llm.openai_utils.billing_utils import get_billing_n, billing_for_async_task
from meutils.schemas.task_types import FluxTaskResponse
from meutils.apis.utils import make_request
from meutils.apis.oneapi.user import get_user_money

from meutils.serving.fastapi.dependencies.auth import parse_token
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi import File, UploadFile, Header, Query, Form, Body, Request

router = APIRouter()
TAGS = ["通用异步任务"]


@router.get("/{biz}/v1/{path:path}")
async def get_task(
        request: Request,

        biz: str = "zhipuai",
        path: str = "request-path",

        headers: dict = Depends(get_headers),
):
    logger.debug(f"biz: {biz} path: {path}")
    logger.debug(bjson(headers))
    logger.debug(bjson(request.query_params))

    # 获取所有查询参数
    params = dict(request.query_params)
    task_id = params.get("id") or params.get("task_id") or params.get("request_id") or Path(path).name  # 路径参数

    # 缓存
    if response := await redis_aclient.get(f"response:{task_id}"):
        response = json.loads(response)
        return response.get("result", {})

    # 上游信息
    upstream_base_url = headers.get('upstream_base_url')
    upstream_path = headers.get('upstream_get_path') or path  # 推荐 path
    # https://open.bigmodel.cn/api/paas/v4/async-result/{id}

    if biz == "fal-ai":  # {model}/requests/{id}: "kling-video/requests/$REQUEST_ID"
        # {model}/requests/{id} => kling-video/requests/c7a92467-c9c9-4404-a1d6-523ea5aa286e
        # {model}/requests/{id}/status => kling-video/requests/c7a92467-c9c9-4404-a1d6-523ea5aa286e/status
        # model, task_id = path.split('/requests/')
        # task_id = task_id.split('/')[0]
        # upstream_path = upstream_path.format(model=model, id=task_id)
        # path
        # "kling-video/requests/d953f062-abd8-4276-9ad4-98e1d926c456/status"
        task_id = path.removesuffix('/').removesuffix("/status").split('/requests/')[-1]
        upstream_path = path

    assert task_id, "task_id is required"
    upstream_api_key = await redis_aclient.get(task_id)
    upstream_api_key = upstream_api_key and upstream_api_key.decode()
    logger.debug(f"upstream_api_key: {upstream_api_key}")
    if not upstream_api_key:
        raise HTTPException(status_code=404, detail="TaskID not found")

    if biz == "fal-ai":
        headers = {"Authorization": f"key {upstream_api_key}"}

    async with atry_catch(f"{biz}/{path}", callback=send_message,
                          upstream_base_url=upstream_base_url, upstream_path=upstream_path):

        response = await make_request(
            base_url=upstream_base_url,
            path=upstream_path,
            api_key=upstream_api_key,

            params=params,
            method=request.method,
            headers=headers,
        )

        # 异步任务信号
        flux_task_response = FluxTaskResponse(id=task_id, result=response)
        data = flux_task_response.model_dump_json(exclude_none=True, indent=4)
        logger.debug(data)
        if flux_task_response.status in {"Ready", "Error"}:
            await redis_aclient.set(f"response:{task_id}", data, ex=3600)

        return response


@router.post("/{biz}/v1/{path:path}")
async def create_task(
        request: Request,

        biz: str = "zhipuai",
        path: str = "request-path",

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

):
    logger.debug(f"biz: {biz} path: {path}")
    logger.debug(bjson(headers))

    # 上游信息
    upstream_model = headers.get('upstream_model')
    upstream_model_key = headers.get('upstream_model_key')  # 从payload中映射

    upstream_base_url = headers.get('upstream_base_url')
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    upstream_path = headers.get('upstream_post_path') or path  # 路径不一致的时候要传 upstream_post_path
    # https://open.bigmodel.cn/api/paas/v4/videos/generations

    # 获取请求体
    payload = await request.json()
    logger.debug(payload)

    # 获取模型名称
    model = (
            payload.get("model")
            or payload.get("model_name")
            or payload.get("search_engine")
            or upstream_model
            or (upstream_model_key and payload.get(upstream_model_key))
            or "UNKNOWN"
    )
    if biz == "fal-ai":
        model = f"fal-{path}".replace("/", "-")  # fal-
        headers = {"Authorization": f"key {upstream_api_key}"}

    # 获取计费次数
    billing_n = get_billing_n(payload)

    async with atry_catch(f"{biz}/{model}", api_key=api_key, callback=send_message,
                          upstream_base_url=upstream_base_url, upstream_path=upstream_path, request=payload):

        # 检查余额
        if user_money := await get_user_money(api_key):
            if user_money < 1:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足")

        # 执行任务
        response = await make_request(
            base_url=upstream_base_url,
            path=upstream_path,
            payload=payload,

            api_key=upstream_api_key,
            method=request.method,
            headers=headers,
            debug=True
        )

        # 计费
        # model = "async"  # 测试
        task_id = (
                response.get("id")
                or response.get("task_id")
                or response.get("request_id")
                or "undefined task_id"
        )
        await billing_for_async_task(model, task_id=task_id, api_key=api_key, n=billing_n)
        await redis_aclient.set(task_id, upstream_api_key, ex=7 * 24 * 3600)  # 轮询任务需要

        if "sync" in biz:  # 针对同步任务：创造异步任务 Ready 信号 注意设置 多模型计费 （单模型用内置接口即可）
            flux_task_response = FluxTaskResponse(id=task_id, result=response, status="Ready")
            data = flux_task_response.model_dump_json(exclude_none=True, indent=4)
            # logger.debug(data)
            await redis_aclient.set(f"response:{task_id}", data, ex=3600)

        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/async')

    app.run()

"""
UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej

curl -X 'POST' 'http://0.0.0.0:8000/async/fal-ai/v1/kling-video/lipsync/audio-to-video' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
     "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
     "audio_url": "https://storage.googleapis.com/falserverless/kling/kling-audio.mp3"
   }'

UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej
REQUEST_ID="842f8b15-06e8-4ee6-8826-c999ba90c6f3"

curl -X 'GET' http://0.0.0.0:8000/async/fal-ai/v1/kling-video/requests/$REQUEST_ID \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json'


UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej
REQUEST_ID="c687b2aa-c83b-4a6a-90a4-bf554755eced"

curl -X 'GET' http://0.0.0.0:8000/async/fal-ai/v1/kling-video/requests/$REQUEST_ID/status \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "UPSTREAM_GET_PATH: $UPSTREAM_GET_PATH" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json'


UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej
REQUEST_ID="31e8f756-29f2-4558-994c-5e4030f263d1"

curl -X 'GET' http://0.0.0.0:8000/async/fal-ai/v1/kling-video/requests/$REQUEST_ID/status \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "UPSTREAM_GET_PATH: $UPSTREAM_GET_PATH" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json'

UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej
REQUEST_ID="31e8f756-29f2-4558-994c-5e4030f263d1"

curl -X 'GET' http://0.0.0.0:8000/async/fal-ai/v1/kling-video/requests/$REQUEST_ID \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "UPSTREAM_GET_PATH: $UPSTREAM_GET_PATH" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json'
    
UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej



curl -X 'GET' 'http://0.0.0.0:8000/async/fal-ai/v1/kling-video/requests/c7a92467-c9c9-4404-a1d6-523ea5aa286e/status' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "UPSTREAM_GET_PATH: $UPSTREAM_GET_PATH" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json'

FAL_KEY=56d8a95e-2fe6-44a6-8f7d-f7f9c83eec24:537f06b6044770071f5d86fc7fcd6d6f
curl --request POST \
  --url https://queue.fal.run/fal-ai/kling-video/lipsync/audio-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
     "audio_url": "https://storage.googleapis.com/falserverless/kling/kling-audio.mp3"
   }'
   

FAL_KEY=56d8a95e-2fe6-44a6-8f7d-f7f9c83eec24:537f06b6044770071f5d86fc7fcd6d6f
REQUEST_ID="31e8f756-29f2-4558-994c-5e4030f263d1"

curl --request GET \
  --url https://queue.fal.run/fal-ai/kling-video/requests/$REQUEST_ID \
  --header "Authorization: Key $FAL_KEY"
"""

"""同步任务
UPSTREAM_BASE_URL="https://ai.gitee.com/v1"
UPSTREAM_API_KEY="5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"
API_KEY=sk-iPNbgHSRkQ9VUb6iAcCa7a4539D74255A6462d29619d6519

curl -X 'POST' 'http://0.0.0.0:8000/async/gitee-sync/v1/moderations' \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "Authorization: Bearer $API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"input":[{"type":"text","text":"...text to classify goes here..."}],"model":"Security-semantic-filtering"}'


# base_url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    # payload = {
    #     "search_query": "周杰伦",
    #     "search_engine": "search_std",
    #     "search_intent": True
    # }
    # api_key = "e130b903ab684d4fad0d35e411162e99.PqyXq4QBjfTdhyCh"
    #
    
UPSTREAM_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
UPSTREAM_API_KEY="e130b903ab684d4fad0d35e411162e99.PqyXq4QBjfTdhyCh"
UPSTREAM_API_KEY="feishu:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=ydUVB1"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=ydUVB1"

API_KEY=sk-iPNbgHSRkQ9VUb6iAcCa7a4539D74255A6462d29619d6519

curl -X 'POST' 'http://0.0.0.0:8000/async/zhipu-sync/v1/web_search' \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "Authorization: Bearer $API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"search_query": "周杰伦",  "search_engine": "search_std", "search_intent": true}'

"""

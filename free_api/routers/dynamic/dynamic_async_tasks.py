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
from meutils.io.files_utils import to_url, get_file_duration, to_bytes
from meutils.llm.check_utils import get_valid_token_for_fal, check_token_for_volc
from meutils.config_utils.lark_utils import get_next_token_for_polling

from meutils.apis.oneapi.user import get_user_money
from meutils.llm.openai_utils.billing_utils import get_billing_n, billing_for_async_task, billing_for_tokens
from meutils.schemas.task_types import FluxTaskResponse
from meutils.apis.utils import make_request

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
    task_id = (
            params.get("id")
            or params.get("task_id")
            or params.get("request_id")
            or params.get("requestId")
            or Path(path).name
    )

    # 缓存
    if response := await redis_aclient.get(f"response:{task_id}"):
        response = json.loads(response)
        return response.get("result", {})

    # 上游信息
    upstream_base_url = headers.get('upstream_base_url', "")
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

    if biz == "fal-ai":  # todo
        headers = {"Authorization": f"key {upstream_api_key}"}

    async with atry_catch(f"{biz}/{path}", callback=send_message,
                          upstream_base_url=upstream_base_url, upstream_path=upstream_path):

        method = "GET"
        payload = None
        if "siliconflow" in upstream_base_url:
            method = "POST"
            payload = {
                "requestId": task_id
            }

        response = await make_request(
            base_url=upstream_base_url,
            api_key=upstream_api_key,

            path=upstream_path,
            payload=payload,

            params=params,
            method=method,
            headers=headers,
        )

        # 异步任务信号
        flux_task_response = FluxTaskResponse(id=task_id, result=response)
        if flux_task_response.status in {"Ready", "Error", "Content Moderated"}:
            if request_data := await redis_aclient.get(f"request:{task_id}"):
                flux_task_response.details['request'] = json.loads(request_data)

            data = flux_task_response.model_dump_json(exclude_none=True, indent=4)

            if "status" not in path:  # fal 除外
                await redis_aclient.set(f"response:{task_id}", data, ex=7 * 24 * 3600)

        # 是否需要 按量计费 todo: request model
        # await billing_for_tokens(model, api_key=api_key, n=billing_n)

        return response


@router.post("/{biz}/v1/{path:path}")
async def create_task(
        request: Request,

        biz: str = "zhipuai",
        path: str = "request-path",

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(f"biz: {biz} path: {path}")  # todo redis 存储信息 注册任务
    logger.debug(bjson(headers))

    # 上游信息
    upstream_model = headers.get('upstream_model')
    upstream_model_key = headers.get('upstream_model_key')  # 从payload中映射

    upstream_base_url = headers.get('upstream_base_url')
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    ######## 轮询 key
    if "volc" in upstream_base_url:
        feishu_url = "https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=rcoDg7"
        upstream_api_key = await get_next_token_for_polling(
            feishu_url=feishu_url,
            from_redis=True,
            ttl=24 * 3600,
            check_token=check_token_for_volc
        ) or upstream_api_key

    elif "ppinfra" in upstream_base_url:
        from meutils.apis.ppio.videos import get_valid_token
        upstream_api_key = await get_valid_token() or upstream_api_key

    elif "fal-ai" in upstream_base_url:  # todo
        upstream_api_key = await get_valid_token_for_fal() or upstream_api_key

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

    # 获取计费次数 todo 重构
    billing_n = get_billing_n(payload, resolution=headers.get("x-resolution"))

    async with atry_catch(f"{biz}/{model}", api_key=api_key, callback=send_message,
                          upstream_base_url=upstream_base_url, upstream_path=upstream_path, request=payload):

        # 检查余额
        if user_money := await get_user_money(api_key):
            if user_money < 1:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足或API-KEY限额")

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
                or response.get("requestId")
                or "undefined task_id"
        )
        # 部分按量计费
        # https://fal.ai/models/fal-ai/topaz/upscale/video
        # https://fal.ai/models/fal-ai/luma-dream-machine/ray-2/reframe
        usage = None
        if biz in {"fal-ai"} and all(i not in path for i in {"voice-clone", "kling-video/lipsync"}):  # 克隆除外

            if url := payload.get("video_url") or payload.get("audio_url") or payload.get("file"):  # 优先判断
                logger.debug(f"按量计费-按时长计费")

                duration = await get_file_duration(Path(url).name, url)

                prompt_tokens = duration * 1000
                usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": 0,
                    "total_tokens": prompt_tokens
                }

            elif any(i in path for i in {"tts", "speech"}) and (text := payload.get("text", "")):  # 按字符收费
                logger.debug(f"按量计费-按字符收费")

                prompt_tokens = len(text.encode())
                usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": 0,
                    "total_tokens": prompt_tokens
                }

            if usage:
                await billing_for_tokens(model, usage, api_key, task_id=task_id)  # 按量走了按次 会超时
                model = "async-task"  # 监听任务用

        await billing_for_async_task(model, task_id=task_id, api_key=api_key, n=billing_n)

        # 新增字段 usage 计费信息
        if usage:
            payload['usage'] = usage
            response['usage'] = usage

        await redis_aclient.set(task_id, upstream_api_key, ex=7 * 24 * 3600)  # 轮询任务需要
        if len(str(payload)) < 10000:  # 存储 request 方便定位问题
            await redis_aclient.set(f"request:{task_id}", json.dumps(payload), ex=7 * 24 * 3600)

        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/async')

    app.run()

"""
    
UPSTREAM_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
UPSTREAM_API_KEY="7d13207e1da54179921a2d037c088f2e.OMMGiUb00uxcryEk"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej

curl -X 'POST' 'http://0.0.0.0:8000/async/zhipuai/v1/videos/generations' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
          "model": "cogvideox-flash",
          "prompt": "比得兔开小汽车，游走在马路上，脸上的表情充满开心喜悦。",
          "duration": 10
        }'

curl -X 'GET' 'http://0.0.0.0:8000/async/zhipuai/v1/async-result/85601750822972284-8573761014975509371' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY"
    
UPSTREAM_BASE_URL="https://api.siliconflow.cn/v1"
UPSTREAM_API_KEY="sk-nffcpzxkdinwvkkmedfqzgsddlmjeyhfzcmkceakhgzvrzuf"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej

curl -X 'POST' 'http://0.0.0.0:8000/async/sf/v1/video/submit' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
          "model": "tencent/HunyuanVideo-HD",
          "prompt": "比得兔开小汽车，游走在马路上，脸上的表情充满开心喜悦。",
          "resolution": "720p"
        }'


curl -X 'GET' 'http://0.0.0.0:8000/async/sf/v1/video/status?id=6b1ow1rsgq6a' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY"

UPSTREAM_BASE_URL="https://queue.fal.run/fal-ai"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=iFRwmM"
API_KEY=sk-R6y5di2fR3OAxEH3idNZIc4sm3CWIS4LAzRfhxSVbhXrrIej

curl -X 'POST' 'http://0.0.0.0:8000/async/fal-ai/v1/vidu/q1/reference-to-video' \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
  "prompt": "A young woman and a monkey inside a colorful house",
  "reference_image_urls": [
    "https://v3.fal.media/files/panda/HDpZj0eLjWwCpjA5__0l1_0e6cd0b9eb7a4a968c0019a4eee15e46.png",
    "https://v3.fal.media/files/zebra/153izt1cBlMU-TwD0_B7Q_ea34618f5d974653a16a755aa61e488a.png",
    "https://v3.fal.media/files/koala/RCSZ7VEEKGFDfMoGHCwzo_f626718793e94769b1ad36d5891864a4.png"
  ],
  "aspect_ratio": "16:9",
  "movement_amplitude": "auto"
}'



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
REQUEST_ID="21700af5-0c80-44ec-8646-cf2d2de82424"

curl -X 'GET' http://0.0.0.0:8000/async/fal-ai/v1/topaz/requests/$REQUEST_ID/status \
    -H "Authorization: Bearer $API_KEY" \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "UPSTREAM_GET_PATH: $UPSTREAM_GET_PATH" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json'

curl -X 'GET' http://0.0.0.0:8000/async/fal-ai/v1/topaz/requests/$REQUEST_ID \
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


UPSTREAM_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
UPSTREAM_API_KEY="8a907822-58ed-4e2f-af25-b7b358e3164c"
UPSTREAM_API_KEY="feishu:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=ydUVB1"
UPSTREAM_API_KEY="redis:https://xchatllm.feishu.cn/sheets/Z59Js10DbhT8wdt72LachSDlnlf?sheet=ydUVB1"
UPSTREAM_API_KEY="8a907822-58ed-4e2f-af25-b7b358e3164c"

API_KEY=sk-iPNbgHSRkQ9VUb6iAcCa7a4539D74255A6462d29619d6519

curl -X 'POST' 'http://0.0.0.0:8000/async/volc/v1/contents/generations/tasks' \
    -H "UPSTREAM_BASE_URL: $UPSTREAM_BASE_URL" \
    -H "UPSTREAM_API_KEY: $UPSTREAM_API_KEY" \
    -H "Authorization: Bearer $API_KEY" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "model": "doubao-seedance-1-0-lite-t2v-250428",
        "content": [
            {
                "type": "text",
                "text": "多个镜头。一名侦探进入一间光线昏暗的房间。他检查桌上的线索，手里拿起桌上的某个物品。镜头转向他正在思索。 --ratio 16:9"
            }
        ]
    }'

"""

"fal-pixverse-v4.5-image-to-video"

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : volcengine
# @Time         : 2025/5/29 17:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.notice.feishu import send_message_for_videos
from meutils.llm.openai_utils import ppu_flow, get_payment_times
from meutils.llm.openai_utils.adapters import chat_for_video
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion
from meutils.llm.openai_utils.billing_utils import get_billing_n, billing_for_async_task, billing_for_tokens, \
    get_billing_model
from meutils.schemas.openai_types import CompletionRequest
from meutils.apis.volcengine_apis import tasks as volcengine_tasks
from meutils.apis.volcengine_apis import videos, videos_nx
from meutils.apis.oneapi.utils import polling_keys
from meutils.schemas.task_types import FluxTaskResponse
from meutils.apis.oneapi.utils import set_async_flux_signal, polling_task

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["火山"]

"""
1.
使用 Action=CVSync2AsyncSubmitTask 接口提交任务，获取到 task_id ；
2.
使用 Action=CVSync2AsyncGetResult 接口 通过 task_id 查询任务结果。

"""
models = {
    'doubao-seedance-2-0_4s_480p',
    'doubao-seedance-2-0_5s_480p',
    'doubao-seedance-2-0_6s_480p',
    'doubao-seedance-2-0_7s_480p',
    'doubao-seedance-2-0_8s_480p',
    'doubao-seedance-2-0_9s_480p',
    'doubao-seedance-2-0_10s_480p',
    'doubao-seedance-2-0_11s_480p',
    'doubao-seedance-2-0_12s_480p',
    'doubao-seedance-2-0_13s_480p',
    'doubao-seedance-2-0_14s_480p',
    'doubao-seedance-2-0_15s_480p',

    'doubao-seedance-2-0_4s_720p',
    'doubao-seedance-2-0_5s_720p',
    'doubao-seedance-2-0_6s_720p',
    'doubao-seedance-2-0_7s_720p',
    'doubao-seedance-2-0_8s_720p',
    'doubao-seedance-2-0_9s_720p',
    'doubao-seedance-2-0_10s_720p',
    'doubao-seedance-2-0_11s_720p',
    'doubao-seedance-2-0_12s_720p',
    'doubao-seedance-2-0_13s_720p',
    'doubao-seedance-2-0_14s_720p',
    'doubao-seedance-2-0_15s_720p'
}


@router.post("/v1")
async def generate(
        request: dict = Body(...),
        Action: str = Query(None, description="接口名称"),
        Version: str = Query(None, description="接口版本"),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    if "task_id" in request:
        return await volcengine_tasks.get_task(request)

    else:
        model = request.get("req_key")
        async with ppu_flow(api_key, post=f"api-volcengine-{model}"):
            task_reponse = await volcengine_tasks.create_task(request)

            return task_reponse


@router.get("/contents/generations/tasks/{task_id}")
async def get_video_task(
        task_id: str,
):
    if api_key := await redis_aclient.get(task_id):
        api_key = api_key.decode()

        get_task = videos_nx.Tasks(api_key=api_key).get_for_volc
        return await polling_task(get_task, task_id)

    else:
        raise HTTPException(status_code=404, detail="TaskID not found")


@router.post("/contents/{dynamic_router:path}")  # 通用类 v1/doubao-seedance-1-0-lite-i2v-250428
async def create_video_task(
        dynamic_router: str,  # /tasks
        request: CompletionRequest,

        api_key: Optional[str] = Depends(get_bearer_token),

        background_tasks: BackgroundTasks = None,
):
    logger.debug(dynamic_router)
    # logger.debug(api_key)
    # logger.debug(bjson(request))
    # chat模式
    if dynamic_router.endswith("chat/completions"):
        if len(api_key) > 128:
            task = videos_nx.Tasks(api_key=api_key)
            video = await task.create_for_volc(request)
            await redis_aclient.set(video.get("id"), api_key, ex=7 * 24 * 3600)

            chunks = await chat_for_video(task.get_for_volc, video.id)
        else:

            response = await videos.create_task(request)
            task_id = response.get("id")  # {'id': 'cgt-20250611152553-r46ql'}

            chunks = await chat_for_video(videos.get_task, task_id)

        return EventSourceResponse(chunks)

    else:
        biz_key = await polling_keys("sd2")
        try:
            video = await videos_nx.Tasks(api_key=biz_key).create_for_volc(request)

        except Exception as e:
            logger.error(f"create video task error: {e}")
            if any(i in str(e) for i in {"QuotaExceeded", "NotLogin"}):
                send_message_for_videos(
                    f"API key {biz_key[:128]} has no quota or not logged in, error: {e}",
                    "seedance2"
                )

                if backup_api_key := await redis_aclient.get("seedance2:backup-api-key"):
                    biz_key = backup_api_key.decode()
                    video = await videos_nx.Tasks(api_key=biz_key).create_for_volc(request)

                else:
                    send_message_for_videos(
                        f"No backup API key available for seedance2, please check the account status.",
                        "seedance2"
                    )
                    raise HTTPException(status_code=500, detail="No available API key")
            else:
                raise HTTPException(status_code=500, detail=str(e))

        task_id = video.get("id")
        await redis_aclient.set(task_id, biz_key, ex=7 * 24 * 3600)

        # 计费
        model = get_billing_model(request)
        if model not in models:
            model = "doubao-seedance-2-0_15s_720p"
        await billing_for_async_task(model, task_id=task_id, api_key=api_key)

        # 备份
        if len(str(request)) < 10000:  # 存储 request 方便定位问题
            await redis_aclient.set(f"request:{task_id}", request.model_dump_json(exclude_none=True), ex=7 * 24 * 3600)

        get_task = videos_nx.Tasks(api_key=biz_key).get_for_volc
        background_tasks.add_task(polling_task, get_task, task_id, 666)

        return video


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

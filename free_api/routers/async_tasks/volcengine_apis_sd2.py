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
from meutils.notice.feishu import send_message_for_videos, send_message_for_volc
from meutils.llm.openai_utils import ppu_flow, get_payment_times

from meutils.llm.openai_utils.billing_utils import get_billing_n, billing_for_async_task, billing_for_tokens, \
    get_billing_model
from meutils.schemas.video_types import SeedRequest
from meutils.apis.volcengine_apis import tasks as volcengine_tasks
from meutils.apis.volcengine_apis import openai_videos_sd2
from meutils.apis.oneapi.utils import polling_keys
from meutils.apis.oneapi.user import get_user_money
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
    'doubao-seedance-2-0-fast_4s_480p',
    'doubao-seedance-2-0-fast_5s_480p',
    'doubao-seedance-2-0-fast_6s_480p',
    'doubao-seedance-2-0-fast_7s_480p',
    'doubao-seedance-2-0-fast_8s_480p',
    'doubao-seedance-2-0-fast_9s_480p',
    'doubao-seedance-2-0-fast_10s_480p',
    'doubao-seedance-2-0-fast_11s_480p',
    'doubao-seedance-2-0-fast_12s_480p',
    'doubao-seedance-2-0-fast_13s_480p',
    'doubao-seedance-2-0-fast_14s_480p',
    'doubao-seedance-2-0-fast_15s_480p',

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
    'doubao-seedance-2-0_15s_720p',

    'doubao-seedance-2-0-fast_4s_720p',
    'doubao-seedance-2-0-fast_5s_720p',
    'doubao-seedance-2-0-fast_6s_720p',
    'doubao-seedance-2-0-fast_7s_720p',
    'doubao-seedance-2-0-fast_8s_720p',
    'doubao-seedance-2-0-fast_9s_720p',
    'doubao-seedance-2-0-fast_10s_720p',
    'doubao-seedance-2-0-fast_11s_720p',
    'doubao-seedance-2-0-fast_12s_720p',
    'doubao-seedance-2-0-fast_13s_720p',
    'doubao-seedance-2-0-fast_14s_720p',
    'doubao-seedance-2-0-fast_15s_720p',

    'doubao-seedance-2-0_4s_1080p',
    'doubao-seedance-2-0_5s_1080p',
    'doubao-seedance-2-0_6s_1080p',
    'doubao-seedance-2-0_7s_1080p',
    'doubao-seedance-2-0_8s_1080p',
    'doubao-seedance-2-0_9s_1080p',
    'doubao-seedance-2-0_10s_1080p',
    'doubao-seedance-2-0_11s_1080p',
    'doubao-seedance-2-0_12s_1080p',
    'doubao-seedance-2-0_13s_1080p',
    'doubao-seedance-2-0_14s_1080p',
    'doubao-seedance-2-0_15s_1080p',
}


@router.get("/contents/generations/tasks/{task_id}")
async def get_video_task(
        task_id: str,
):
    if api_key := await redis_aclient.get(task_id):
        api_key = api_key.decode()

        get_task = openai_videos_sd2.Tasks(api_key=api_key)._get
        return await polling_task(get_task, task_id)

    else:
        raise HTTPException(status_code=404, detail="TaskID not found")


@router.post("/contents/{dynamic_router:path}")  # 通用类 v1/doubao-seedance-1-0-lite-i2v-250428
async def create_video_task(
        dynamic_router: str,  # /tasks
        request: SeedRequest,

        api_key: Optional[str] = Depends(get_bearer_token),

        background_tasks: BackgroundTasks = None,
):
    # 检查余额
    if user_money := await get_user_money(api_key):
        if user_money < 1:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足或API-KEY限额")

    with_video = None
    if request.model.startswith("doubao-seedance-2-0"):
        biz_key = await polling_keys("sd2")
        with_video = "reference_video" in str(request.content)
    else:
        biz_key = await polling_keys("volc")

    try:
        video = await openai_videos_sd2.Tasks(api_key=biz_key)._create(request)

    except Exception as e:
        if any(i in str(e) for i in {"QuotaExceeded", "overdue"}):  # todo 未激活 or 404 获取key  lite获取新key
            send_message_for_volc(biz_key, "sd2欠费key")
            biz_key = await polling_keys("sd2:bk")
            video = await openai_videos_sd2.Tasks(api_key=biz_key)._create(request)
        else:
            raise e

    task_id = video.get("id")
    await redis_aclient.set(task_id, api_key, ex=7 * 24 * 3600)

    # 计费
    model = get_billing_model(request)
    if model not in models:
        model = "doubao-seedance-1-5_5s_720p"

    if with_video:  # 视频输入单独计费
        model = model.replace("2-0", "2-0-v2v")

    await billing_for_async_task(model, task_id=task_id, api_key=api_key)

    # 备份
    if len(str(request)) < 10000:  # 存储 request 方便定位问题
        await redis_aclient.set(f"request:{task_id}", request.model_dump_json(exclude_none=True), ex=7 * 24 * 3600)

    get_task = openai_videos_sd2.Tasks(api_key=biz_key)._get
    background_tasks.add_task(polling_task, get_task, task_id, 666)

    return video


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/doubao/api/v3')

    app.run()

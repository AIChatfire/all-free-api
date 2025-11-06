#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : minimax
# @Time         : 2025/8/8 17:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils.billing_utils import billing_for_async_task
from meutils.apis.models import make_billing_model
from meutils.apis.minimax import videos
from meutils.apis.oneapi.user import get_user_money
from meutils.schemas.task_types import FluxTaskResponse

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/files/retrieve")
async def get_task(
        file_id: str = Query(),
):
    return await videos.get_file(file_id)


@router.get("/query/video_generation")  # GET https://api.minimax.chat/v1/query/video_generation?task_id={task_id}
async def get_task(
        task_id: str,
):
    response = await videos.get_task(task_id)
    # 异步任务信号
    flux_task_response = FluxTaskResponse(id=task_id, result=response)
    if flux_task_response.status in {"Ready", "Error", "Content Moderated"}:
        if request_data := await redis_aclient.get(f"request:{task_id}"):
            flux_task_response.details['request'] = json.loads(request_data)

        data = flux_task_response.model_dump_json(exclude_none=True, indent=4)
        await redis_aclient.set(f"response:{task_id}", data, ex=7 * 24 * 3600)

    return response


@router.post("/video_generation")  # POST https://api.minimax.chat/v1/video_generation
async def create_task(
        request: dict,
        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),
):
    # 检查余额
    if user_money := await get_user_money(api_key):
        if user_money < 1:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足或API-KEY限额")

    # 执行
    response = await videos.create_task(request=request)

    # 计费
    billing_model = make_billing_model("minimax", request)
    if task_id := response.get("task_id"):
        await billing_for_async_task(billing_model, task_id=task_id, api_key=api_key)

        if len(str(request)) < 10000:  # 存储 request 方便定位问题
            await redis_aclient.set(f"request:{task_id}", json.dumps(request), ex=7 * 24 * 3600)


    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/minimax/v1')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : jimeng
# @Time         : 2025/5/7 14:29
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message
from meutils.llm.openai_utils.billing_utils import get_billing_n, billing_for_async_task
from meutils.schemas.task_types import FluxTaskResponse
from meutils.apis.oneapi.user import get_user_money
from meutils.apis.jimeng import videos

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["Video"]


@router.get("/tasks/{task_id}")
async def get_task(
        task_id: str,
):
    response = await videos.get_task(task_id)
    response = response.model_dump(exclude_none=True)

    # 异步任务信号
    flux_task_response = FluxTaskResponse(id=task_id, result=response)
    if flux_task_response.status in {"Ready", "Error", "Content Moderated"}:
        if request_data := await redis_aclient.get(f"request:{task_id}"):
            flux_task_response.details['request'] = json.loads(request_data)

        data = flux_task_response.model_dump_json(exclude_none=True, indent=4)
        await redis_aclient.set(f"response:{task_id}", data, ex=3600)

    return response

    ##############
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    task_response = await videos.get_task(task_id, token)
    return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/tasks")
async def create_task(
        request: videos.VideoRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    # 检查余额
    if user_money := await get_user_money(api_key):
        if user_money < 1:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足")

    # 获取计费次数
    model = "jimeng-video-3.0"
    payload = request.model_dump_json(exclude_none=True, indent=4)
    billing_n = get_billing_n(request)
    async with atry_catch(f"jimeng-videos", api_key=api_key, callback=send_message, request=payload):

        # 执行
        response = await videos.create_task(request)
        response = response.model_dump(exclude_none=True)

        # 计费
        # model = "async"  # 测试
        task_id = (
                response.get("id")
                or response.get("task_id")
                or response.get("request_id")
                or "undefined task_id"
        )
        await billing_for_async_task(model, task_id=task_id, api_key=api_key, n=billing_n)
        if len(str(payload)) < 10000:  # 存储 request 方便定位问题
            await redis_aclient.set(f"request:{task_id}", payload, ex=7 * 24 * 3600)

        return response

    # async with ppu_flow(api_key, post="api-videos-seedream-3.0", n=N):
    #     task_response = await videos.create_task(request)
    #
    #     logger.debug(task_response)
    #
    #     await redis_aclient.set(task_response.task_id, task_response.system_fingerprint, ex=7 * 24 * 3600)
    #     return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

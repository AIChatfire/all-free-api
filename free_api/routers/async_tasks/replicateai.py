#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : replicate
# @Time         : 2024/11/15 18:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 可当作通用异步任务接口

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.db.orm import update_or_insert
from meutils.schemas.db.oneapi_types import Hero, Tasks, STATUSES
from meutils.apis.oneapi.user import get_api_key_log

from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.replicate_types import ReplicateRequest, ReplicateResponse
from meutils.apis.replicateai import raw as replicate

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["replicate"]


# 数据库获取任务 https://api.chatfire.cn/replicate/v1/predictions/d42c7e90a577bdec0a68797e77a8e0d8

# @router.get("/{path:path}/{task_id}") # 通用
@router.get("/predictions/{task_id}")
@alru_cache(ttl=15)
async def get_task(
        task_id: str,
        backgroundtasks: BackgroundTasks = BackgroundTasks,

):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    task_data = await replicate.get_task(task_id, token)  # 不更新状态 只做轮询
    return task_data.model_dump(exclude_none=True, exclude={"system_fingerprint"})


# /models/black-forest-labs/flux-1.1-pro/predictions
@router.post("/models/{model:path}/predictions")
async def create_task(
        model: str,
        request: ReplicateRequest,

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth and auth.credentials or None

    request.ref = model
    logger.debug(request.model_dump_json(indent=4))

    user_id = None
    if onelog := await get_api_key_log(api_key):
        user_id = onelog[0]['user_id']

    n = request.input.get('num_outputs', 1)  # n张图片
    async with ppu_flow(api_key, post=f"api-replicate-{request.ref.split('/')[-1]}", n=n):
        data = await replicate.create_task(request)

        async def update_fn(task: Tasks):
            if task.status in {"SUCCESS", "FAILURE"}: return False  # 跳出轮询

            task_data = await replicate.get_task(data.id, data.system_fingerprint)

            task.data = task_data.model_dump(exclude_none=True, exclude={"system_fingerprint"})
            task.status = STATUSES.get(task_data.status.lower(), "UNKNOWN")
            task.progress = float(task.progress.strip('%')) + 5
            if task.status == "SUCCESS":
                task.progress = "100%"
            elif task.status == "FAILURE":
                task.fail_reason = "查看详情"

            task.updated_at = int(time.time())
            task.finish_time = int(time.time())  # 不是实际时间

        kwargs = {
            "task_id": data.id,
            "user_id": user_id,
            "platform": "replicate",
            "action": request.ref,
        }
        backgroundtasks.add_task(update_or_insert, Tasks, kwargs, update_fn, 10)

        await redis_aclient.set(data.id, data.system_fingerprint, ex=7 * 24 * 3600)
        return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})


# sqlalchemy.exc.InvalidRequestError: Incorrect number of values in identifier to formulate primary key for session.get(); primary key columns are 'tasks.id'

if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

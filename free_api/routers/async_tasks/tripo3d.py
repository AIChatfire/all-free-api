#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : kling
# @Time         : 2024/9/24 09:47
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.tripo3d import images
from meutils.schemas.tripo3d_types import ImageRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["图片生成"]


@router.get("/task/{task_id}")
@alru_cache(ttl=15)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if token is None:
        raise HTTPException(status_code=404, detail="TaskID not found")

    data = await images.get_task(task_id, token)
    return data


@router.post("/task")
async def create_task(
        request: ImageRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        vip: Optional[bool] = Query(True)
):
    api_key = auth and auth.credentials or None

    N = 1
    async with ppu_flow(api_key, post="api-tripo3d", n=N):
        images.send_message(request)
        task = await images.create_task(request, vip=vip)
        images.send_message(task)

        for task_id in task.task_ids:
            await redis_aclient.set(task_id, task.system_fingerprint, ex=7 * 24 * 3600)

        return task.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fal
# @Time         : 2025/1/15 19:05
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.fal import kling_videos

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["Video"]


@router.get("/tasks")  # {task_id:path} 反代有问题
@alru_cache(ttl=30)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    task_response = await kling_videos.get_task(task_id, token)
    return task_response


@router.post("/tasks")
async def create_task(
        request: kling_videos.VideoRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    N = request.duration // 5
    async with ppu_flow(api_key, post=f"api-{request.model}", n=N):  # kling-video/v2/master/image-to-video
        task_response = await kling_videos.create_task(request)

        await redis_aclient.set(task_response.task_id, task_response.system_fingerprint, ex=7 * 24 * 3600)

        return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

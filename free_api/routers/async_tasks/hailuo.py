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

from meutils.apis.hailuoai import videos
from meutils.schemas.hailuo_types import VideoRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/query/video_generation")  # GET https://api.minimax.chat/v1/query/video_generation?task_id={task_id}
@alru_cache(ttl=30)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    data = await videos.get_task(task_id, token)
    return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/video_generation")  # POST https://api.minimax.chat/v1/video_generation
async def create_task(
        request: VideoRequest,
        auth: Optional[str] = Depends(get_bearer_token),

):
    api_key = auth

    N = 1
    async with ppu_flow(api_key, post="official-api-hailuo-video", n=N):
        videos.send_message(request)
        task = await videos.create_task(request)
        videos.send_message(task)

        await redis_aclient.set(task.task_id, task.system_fingerprint, ex=30 * 24 * 3600)

        return task.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

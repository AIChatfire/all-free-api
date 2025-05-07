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
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.jimeng import videos

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["Video"]


@router.get("/tasks/{task_id}")
@alru_cache(ttl=30)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    logger.debug(token)

    task_response = await images.get_task(task_id, token)
    return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/tasks")
async def create_task(
        request: videos.VideoRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    N = request.duration // 5
    async with ppu_flow(api_key, post="api-videos-seedream-3.0", n=N):
        task_response = await videos.create_task(request)

        logger.debug(task_response)

        await redis_aclient.set(task_response.task_id, task_response.system_fingerprint, ex=7 * 24 * 3600)
        return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

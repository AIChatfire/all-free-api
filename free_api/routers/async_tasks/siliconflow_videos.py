#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : hunyaun
# @Time         : 2024/12/13 13:03
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.siliconflow import videos as siliconflow_videos

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/videos/{task_id}")
@alru_cache(ttl=15)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    logger.debug(token)
    if not token:
        raise HTTPException(status_code=404, detail="Task ID not found")

    task_reponse = await siliconflow_videos.get_task(task_id, token)

    return task_reponse


@router.post("/videos")
async def generate(
        request: siliconflow_videos.VideoRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))

    async with ppu_flow(api_key, post=f"api-videos-{request.model}"):
        task_reponse = await siliconflow_videos.create_task(request)

        await redis_aclient.set(task_reponse.task_id, task_reponse.system_fingerprint, ex=7 * 24 * 3600)
        return task_reponse.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

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
from meutils.schemas.task_types import TaskType, Task

from meutils.apis.kling import images, videos
from meutils.schemas.kling_types import ImageRequest, VideoRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["kling"]


@router.get("/{action}/{action2}/{task_id}")
@alru_cache(ttl=15)
async def get_task(
        action: str,
        action2: str,
        task_id: str,  # kling-xxx
        oss: Optional[str] = Query(None),
        whether_to_transfer: bool = Query(True),
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if token is None:
        raise HTTPException(status_code=404, detail="TaskID not found")

    task_type = None
    if "-" in task_id:
        task_type, _ = task_id.rsplit("-", 1)  # 区分业务

    if task_type is None:
        pass

    elif task_type.startswith(TaskType.kling_image):
        data = await images.get_task(task_id, token, oss=oss)
        return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})

    elif task_type.startswith(TaskType.kling_video):
        data = await videos.get_task(task_id, token, oss=oss)
        return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/images/generations")
async def create_task_images(
        request: ImageRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        vip: Optional[bool] = Query(True)
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    async with ppu_flow(api_key, post="official-api-kling-image", n=request.n):
        task = await images.create_task(request, vip=vip)

        if task.code == 0:
            task_id = task.data.task_id
            images.send_message(f"images 任务提交成功：\n\n{task_id}")
            await redis_aclient.set(task_id, task.system_fingerprint, ex=7 * 24 * 3600)

        return task.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/videos/text2video")
async def create_task_text2video(
        request: VideoRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        vip: Optional[bool] = Query(True)
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    n = (1 if request.duration < 5 else 2) * request.n
    if request.mode == 'pro':
        n *= 3.5

    async with ppu_flow(api_key, post="official-api-kling-video", n=int(n)):
        task = await videos.create_task(request, vip=vip)

        if task.code == 0:
            task_id = task.data.task_id
            videos.send_message(f"text2video 任务提交成功：\n\n{task_id}")
            await redis_aclient.set(task_id, task.system_fingerprint, ex=7 * 24 * 3600)

        return task.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/videos/image2video")
async def create_task_image2video(
        request: VideoRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        vip: Optional[bool] = Query(True)
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    n = 1 if request.duration < 5 else 2
    if request.mode == 'pro':
        n *= 3.5

    async with ppu_flow(api_key, post="official-api-kling-video", n=int(n)):
        task = await videos.create_task(request, vip=vip)

        if task.code == 0:
            task_id = task.data.task_id
            videos.send_message(f"image2video 任务提交成功：\n\n{task_id}")
            await redis_aclient.set(task_id, task.system_fingerprint, ex=7 * 24 * 3600)

        return task.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

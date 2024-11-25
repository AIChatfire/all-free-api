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
from meutils.db.orm import update_or_insert

from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.task_types import TaskType, Task
from meutils.schemas.db.oneapi_types import Tasks, STATUSES
from meutils.apis.oneapi.user import get_api_key_log

from meutils.apis.kling import images, videos, kolors_virtual_try_on
from meutils.schemas.kling_types import STATUSES, ImageRequest, VideoRequest, TryOnRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/{action}/{action2}/{task_id}")
@alru_cache(ttl=30)
async def get_task(
        action: str,
        action2: str,
        task_id: str,  # kling-xxx
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    task_type = action
    if "-" in task_id:
        task_type, _ = task_id.rsplit("-", 1)  # 区分业务

    if task_type is None:
        pass

    elif task_type.startswith(TaskType.kling_image):
        data = await images.get_task(task_id, token)
        return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})

    elif task_type.startswith(TaskType.kling_video):
        data = await videos.get_task(task_id, token)
        return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})

    if action2 == "kolors-virtual-try-on":  # 官方接口
        data = await kolors_virtual_try_on.get_task(task_id, token)
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


@router.post("/images/kolors-virtual-try-on")
async def create_task_image2video(
        request: TryOnRequest,

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,

):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    user_id = None
    if onelog := await get_api_key_log(api_key):
        user_id = onelog[0]['user_id']

    async with ppu_flow(api_key, post="official-api-kolors-virtual-try-on"):
        data = await kolors_virtual_try_on.create_task(request)
        task_id = data.data.task_id

        async def update_fn(task: Tasks):
            if task.status == "SUCCESS": return False  # 跳出轮询

            task_data = await kolors_virtual_try_on.get_task(task_id, data.system_fingerprint)

            task.data = task_data.model_dump(exclude_none=True, exclude={"system_fingerprint"})
            task.status = STATUSES.get(task_data.data.task_status.lower(), "UNKNOWN")
            task.progress = time.time() / 10 % 100

            if task.status == "SUCCESS":
                task.progress = "100%"
            elif task.status == "FAILURE":
                task.fail_reason = "查看详情"

            task.updated_at = int(time.time())
            task.finish_time = int(time.time())  # 不是实际时间

        kwargs = {
            "task_id": task_id,
            "user_id": user_id,
            "platform": "kling",
            "action": request.model_name,
        }
        backgroundtasks.add_task(update_or_insert, Tasks, kwargs, update_fn, 100)

        await redis_aclient.set(task_id, data.system_fingerprint, ex=7 * 24 * 3600)
        return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})


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

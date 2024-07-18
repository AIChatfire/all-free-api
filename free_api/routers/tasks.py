#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : task
# @Time         : 2024/7/11 13:35
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.task_types import TaskType, Task
from meutils.schemas.kuaishou_types import KlingaiVideoRequest, Camera
from meutils.apis.kuaishou import klingai_video
from meutils.schemas.runwayml_types import RunwayRequest
from meutils.apis.runwayml import gen
from meutils.schemas.suno_types import SunoAIRequest, LyricsRequest
from meutils.apis.sunoai import suno

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, Depends, BackgroundTasks, Request, Query, Body, Header, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter()
TAGS = ["异步任务"]


@router.get("/tasks/{task_id}")
async def get_tasks(
        task_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth and auth.credentials or None

    task_type = None
    if "-" in task_id:
        task_type, _ = task_id.split("-", 1)  # 区分业务

    data = {}
    if task_type is None:  # 通用业务：默认从redis获取
        data = await redis_aclient.get(task_id)

    elif task_type == TaskType.kling:  # 从个业务线获取: 获取token => 在请求接口 （kling-taskid: cookie）
        async with ppu_flow(api_key, post="ppu-0001"):

            token = await redis_aclient.get(task_id)
            token = token and token.decode()

            data = await klingai_video.get_task(task_id, token)
            return data

    elif task_type == TaskType.runwayml:
        async with ppu_flow(api_key, post="ppu-0001"):

            token = await redis_aclient.get(task_id)
            token = token and token.decode()

            data = await gen.get_task(task_id, token)
            return data

    elif task_type == TaskType.suno:
        async with ppu_flow(api_key, post="ppu-0001"):

            token = await redis_aclient.get(task_id)
            token = token and token.decode()

            data = await suno.get_task(task_id, token)
            return data

    elif task_type == TaskType.fish:  # todo: 语音克隆
        async with ppu_flow(api_key, post="ppu-0001"):

            token = await redis_aclient.get(task_id)
            token = token and token.decode()

            data = await suno.get_task(task_id, token)
            return data

    return JSONResponse(content=data, media_type="application/json")


@router.post(f"/tasks/{TaskType.kling}")
async def create_tasks(
        request: KlingaiVideoRequest,
        # task_type: TaskType,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        feishu_url: Optional[str] = Header(None),  # 指定某个token

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))
    logger.debug(feishu_url)

    api_key = auth and auth.credentials or None
    task_type = TaskType.kling

    async with ppu_flow(api_key, post="api-kling-video"):
        task = await klingai_video.create_task(request, feishu_url=feishu_url)
        if task and task.status:
            klingai_video.send_message(f"任务提交成功：\n\n{task_type}-{task.id}")
            task.id = f"{task_type}-{task.id}"

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})

        raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=task)


@router.post(f"/tasks/{TaskType.runwayml}")
async def create_tasks(
        request: RunwayRequest,
        # task_type: TaskType,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None
    task_type = TaskType.runwayml

    async with ppu_flow(api_key, post="api-runwayml-gen3"):
        task = await gen.create_task(request)
        if task and task.status:
            gen.send_message(f"任务提交成功：\n\n{task_type}-{task.id}")

            task.id = f"{task_type}-{task.id}"
            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})
        elif task is None:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=task)

        else:
            raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=task)


@router.post(f"/tasks/{TaskType.suno}")
async def create_tasks(
        request: SunoAIRequest,
        # task_type: TaskType,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None
    task_type = TaskType.suno
    token = request.continue_clip_id and await redis_aclient.get(request.continue_clip_id)  # 针对上传的音频
    token = token and token.decode()

    async with ppu_flow(api_key, post="api-sunoai-chirp"):
        task = await suno.create_task(request, token)
        if task and task.status:
            gen.send_message(f"任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})

        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=task)


@router.post(f"/tasks/{TaskType.lyrics}")
async def create_tasks(
        request: LyricsRequest,
        # task_type: TaskType,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None
    task_type = TaskType.lyrics

    async with ppu_flow(api_key, post="api-sunoai-lyrics"):
        data = await suno.generate_lyrics(prompt=request.prompt)
        return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

# print(arun(redis_aclient.get("kling-28377631")).decode())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2024/9/13 09:52
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.task_types import TaskType, Task

from meutils.schemas.video_types import VideoRequest
from meutils.apis.chatglm import glm_video_api

from meutils.schemas.vidu_types import ViduRequest, ViduUpscaleRequest
from meutils.apis.vidu import vidu_video

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/async-result/{task_id}")  # todo: sd3 兜底
async def get_task(
        task_id: str,
        response_format: Optional[str] = Query(None),
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="Task ID not found")

    task_type = None
    if "-" in task_id:
        task_type, _ = task_id.split("-", 1)  # 区分业务

    if task_type is None:
        pass

    elif task_type.startswith(TaskType.cogvideox):
        data = await glm_video_api.get_task(task_id, token)
        return data

    elif task_type.startswith(TaskType.vidu):
        data = await vidu_video.get_task(task_id, token)
        return data  # todo: 兼容格式


@router.post("/videos/generations")  # todo: sd3 兜底
async def generate(
        request: VideoRequest,
        auth: Optional[str] = Depends(get_bearer_token),
):
    api_key = auth

    logger.debug(request.model_dump_json(indent=4))

    if request.model.startswith("cogvideox"):
        async with ppu_flow(api_key, post="official-api-cogvideox"):
            task_type = TaskType.cogvideox_vip

            task = await glm_video_api.create_task(request)
            glm_video_api.send_message(f"{task_type} 任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
            return task.model_dump(exclude={"system_fingerprint"})

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
from meutils.apis.kuaishou import klingai_video
from meutils.llm.openai_utils import ppu_flow
from meutils.schemas.task_types import TaskType, Task
from meutils.schemas.kuaishou_types import KlingaiVideoRequest, Camera
from meutils.config_utils.lark_utils import get_next_token_for_polling

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header, HTTPException, status
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

    elif task_type == "kling":  # 从个业务线获取: 获取token => 在请求接口 （kling-taskid: cookie）
        async with ppu_flow(api_key, post="ppu-001"):

            token = await redis_aclient.get(task_id)  # bytes
            token = token and token.decode()

            logger.debug(token)  # 28383134

            data = await klingai_video.get_task(task_id, token)
            return data

    elif task_type == "suno":
        pass

    return JSONResponse(content=data, media_type="application/json")


@router.post("/tasks/{task_type}")
async def submit_tasks(
        request: Union[KlingaiVideoRequest],
        task_type: TaskType,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        upstream_base_url: Optional[str] = Header(None),
        upstream_api_key: Optional[str] = Header(None),
        downstream_base_url: Optional[str] = Header(None),

        background_tasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth and auth.credentials or None

    if task_type == "kling":
        async with ppu_flow(api_key, post="kling-video"):
            task = await klingai_video.submit_task(request)  # task_id, token
            if task.status:
                klingai_video.send_message(f"任务提交成功：{task.id}")
                task.id = f"{task_type}-{task.id}"

                await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)
                return task.model_dump(exclude={"system_fingerprint"})

            raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=task.data)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

# print(arun(redis_aclient.get("kling-28377631")).decode())

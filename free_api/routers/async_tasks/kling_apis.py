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
from meutils.schemas.task_types import STATUSES, TaskType, Task
from meutils.apis.kling.kling_apis import tasks

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Body, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["可灵官方api"]


@router.get("/v1/{action}/{action2}/{task_id}")
async def get_task(
        action: str,
        action2: str,
        task_id: str,  # kling-xxx
):
    path = f"/v1/{action}/{action2}"
    return await tasks.get_task(path, task_id)


@router.post("/{path:path}")
async def create_task(
        path: str,

        request: dict = Body(...),
):
    payload = request

    return await tasks.create_task(path, payload)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '')

    app.run()

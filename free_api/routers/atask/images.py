#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : volcengine
# @Time         : 2025/5/29 17:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *

from meutils.schemas.image_types import ImageRequest
from meutils.apis.async_tasks import images

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["tasks"]

"""


"""


@router.get("/tasks/{task_id}")
async def get_task(
        task_id: str,
):
    return await images.Tasks.get(task_id)


@router.post("/{dynamic_router:path}")  # 通用类 v1/doubao-seedance-1-0-lite-i2v-250428
async def create_task(
        dynamic_router: str,  # /tasks
        request: ImageRequest,

        api_key: Optional[str] = Depends(get_bearer_token),

        background_tasks: BackgroundTasks = None,
):
    logger.debug(dynamic_router)

    task = images.Tasks(api_key=api_key)

    return await task.create(request)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/async/v1')

    app.run()

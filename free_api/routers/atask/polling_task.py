#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : polling_task
# @Time         : 2026/6/11 16:30
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 



from meutils.apis.async_tasks import images

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["tasks"]



@router.get("/{task_id}") # f"https://polling-url.atask.cn/{task_id}"
async def get_task(
        task_id: str,
):
    return await images.Tasks.get(task_id)
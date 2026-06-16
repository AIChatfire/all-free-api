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
from meutils.db.redis_db import redis_aclient

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["tasks"]



@router.get("/{task_id}") # f"https://polling-url.atask.cn/{task_id}"
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="Task ID not found")

    return await images.Tasks.get(task_id)
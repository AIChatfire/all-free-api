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

from meutils.apis.oneapi.user import get_api_key_log

from meutils.apis.kling import images, videos, kolors_virtual_try_on
from meutils.schemas.kling_types import STATUSES, ImageRequest, VideoRequest, TryOnRequest

#
from meutils.async_task.tasks import kling
from meutils.schemas.task_types import TaskResponse
from meutils.async_task.utils import get_task, create_task

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/{action}/{action2}/{task_id}")  # todo: 通用
@alru_cache(ttl=30)
async def _get_task(
        action: str,
        action2: str,
        task_id: str,  # kling-xxx

        api_key: Optional[str] = Depends(get_bearer_token),

):
    logger.debug(api_key)

    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    ########################################################################################
    user_id = None
    if onelog := await get_api_key_log(api_key):  # todo: 优化查询
        user_id = onelog[0]['user_id']

    filter_kwargs = {
        "task_id": task_id,
        "user_id": user_id,
        "platform": "kling",
        "action": action2,
    }
    ########################################################################################

    if action2 == "kolors-virtual-try-on":  # 官方接口
        data = await get_task(task_id, kolors_virtual_try_on.get_task, filter_kwargs)  # 排队获取任务
        return data  # .model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/images/kolors-virtual-try-on")
async def _create_task(
        request: TryOnRequest,

        api_key: Optional[str] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    async with ppu_flow(api_key, post="official-api-kolors-virtual-try-on"):
        task_response = await create_task(kling.create_task, request)

        return task_response  # .model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

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
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.oneapi.user import get_api_key_log

from meutils.async_task.utils import get_task, create_task
from meutils.async_task.tasks import hailuo
from meutils.schemas.hailuo_types import VideoRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频生成"]


@router.get("/query/video_generation")  # GET https://api.minimax.chat/v1/query/video_generation?task_id={task_id}
@alru_cache(ttl=30)
async def _get_task(
        task_id: str,

        api_key: Optional[str] = Depends(get_bearer_token),
        background_tasks: BackgroundTasks = BackgroundTasks,
):
    data = await get_task(task_id, hailuo.get_task, background_tasks=background_tasks)
    return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/video_generation")  # POST https://api.minimax.chat/v1/video_generation
async def _create_task(
        request: VideoRequest,

        api_key: Optional[str] = Depends(get_bearer_token),
        background_tasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    ########################################################################################
    user_id = None
    if onelog := await get_api_key_log(api_key):  # todo: 优化查询
        user_id = onelog[0]['user_id']

    ########################################################################################

    async with ppu_flow(api_key, post="official-api-hailuo-video"):
        task_response = await create_task(hailuo.create_task, request)

        task_id = task_response.task_id
        filter_kwargs = {
            "task_id": task_id,
            "user_id": user_id,
            "platform": "minimax",
            "action": f"hailuo-{request.model}",
        }
        background_tasks.add_task(get_task, task_id, hailuo.get_task, filter_kwargs)  ##### 实际并没有执行

        logger.debug(task_response)

        return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

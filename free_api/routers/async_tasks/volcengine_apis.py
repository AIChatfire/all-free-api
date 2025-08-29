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
from meutils.llm.openai_utils import ppu_flow, get_payment_times
from meutils.llm.openai_utils.adapters import chat_for_video
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion

from meutils.schemas.openai_types import CompletionRequest
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.apis.volcengine_apis import tasks as volcengine_tasks
from meutils.apis.volcengine_apis import videos

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["火山"]

"""
1.
使用 Action=CVSync2AsyncSubmitTask 接口提交任务，获取到 task_id ；
2.
使用 Action=CVSync2AsyncGetResult 接口 通过 task_id 查询任务结果。

"""


@router.post("/v1")
async def generate(
        request: dict = Body(...),
        Action: str = Query(None, description="接口名称"),
        Version: str = Query(None, description="接口版本"),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    if "task_id" in request:
        return await volcengine_tasks.get_task(request)

    else:
        model = request.get("req_key")
        async with ppu_flow(api_key, post=f"api-volcengine-{model}"):
            task_reponse = await volcengine_tasks.create_task(request)

            return task_reponse


@router.get("/contents/generations/tasks/{task_id}")  # 通用类
async def get_video_task(
        task_id: str,
):
    return await videos.get_task(task_id)


@router.post("/contents/{dynamic_router:path}")  # 通用类 v1/doubao-seedance-1-0-lite-i2v-250428
async def create_video_task(
        dynamic_router: str,  # /tasks
        request: CompletionRequest,

        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(dynamic_router)
    # logger.debug(bjson(request))
    # chat模式
    if dynamic_router.endswith("chat/completions"):
        response = await videos.create_task(request)
        task_id = response.get("id")  # {'id': 'cgt-20250611152553-r46ql'}

        chunks = await chat_for_video(videos.get_task, task_id)
        return EventSourceResponse(chunks)

    N = get_payment_times(request)
    # N = 0

    dynamic_model = f"api-{request.model}"
    if resolution := request.model_dump().get("resolution"):
        dynamic_model += f"-{resolution}"
    else:
        for resolution in {"480p", "720p", "1080p"}:
            if resolution in str(request):
                dynamic_model += f"-{resolution}"
                break

    async with atry_catch(f"{dynamic_model}", api_key=api_key, callback=send_message, request=request):

        async with ppu_flow(api_key, post=dynamic_model, dynamic=True, n=N):
            response = await videos.create_task(request)
            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : billing
# @Time         : 2025/6/24 08:59
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.apis.utils import make_request

from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from meutils.schemas.openai_types import CompletionRequest, chat_completion, chat_completion_chunk, \
    chat_completion_chunk_stop

from meutils.schemas.image_types import ImageRequest, ImagesResponse

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["usage"]


@router.post("/v1/{dynamic_router:path}")  # 这个动态计费有点问题
async def create_chat_completions(
        dynamic_router: str,
        request: dict,  # 有些参数传不进 oneapi 用替代方案
):
    logger.debug(bjson(request))

    usage = request.get('extra_body') or request.get('extra_fields')  # 没传进去有点奇怪
    if "images/generations" in dynamic_router:  # image 模式计费
        return ImagesResponse(usage=usage)

    chat_completion.usage = usage
    return chat_completion

    # if "chat/completions" in dynamic_router:  # chat 模式计费
    #     request = CompletionRequest(**request)
    #
    #     if request.stream:
    #         chat_completion_chunk.usage = request.usage
    #
    #         def gen():
    #
    #             yield chat_completion_chunk
    #             yield chat_completion_chunk_stop.model_dump_json()
    #             yield "[DONE]"  # 兼容标准格式
    #
    #         return EventSourceResponse(gen())
    #     else:
    #         chat_completion.usage = request.usage
    #
    #         return chat_completion
    #


@router.post("/oai/v1/chat/completions")  # 按量计费
async def create_chat_completions(
        request: CompletionRequest,  # 有些参数传不进 oneapi 用替代方案
):
    logger.debug(bjson(request))

    chat_completion.usage = request.extra_body

    return chat_completion


@router.post("/oai/v1/images/generations")  # 按量计费
async def create_chat_completions(
        request: ImageRequest,  # 有些参数传不进 oneapi 用替代方案
):
    logger.debug(bjson(request))

    return ImagesResponse(usage=request.extra_fields)


@router.get("/async/flux/v1/get_result")  # todo: 缓存，选择性缓存（成功 失败）
async def get_async_task(id: str):
    """传递状态 https://docs.bfl.ai/api-reference/utility/get-result
            TaskStatusNotStart              = "NOT_START"
            TaskStatusSubmitted             = "SUBMITTED"
            TaskStatusQueued                = "QUEUED"
            TaskStatusInProgress            = "IN_PROGRESS"
            TaskStatusFailure               = "FAILURE"  # todo: 补偿积分+状态记录
            TaskStatusSuccess               = "SUCCESS"
            TaskStatusUnknown               = "UNKNOWN
    """

    # ["Ready", "Error", "Failed", "Pending"]
    # Task not found, Pending, Request Moderated, Content Moderated, Ready, Error
    task_id = id
    status = "Pending"
    progress = 0
    if 'chatfire-' in task_id:  # 仅仅测试使用
        task_id, status, progress = task_id.removeprefix("chatfire-").split('-')

    return {
        "id": task_id,
        "status": status,
        "result": {},
        "progress": int(progress),
        "details": {}
    }


@router.post("/async/flux/v1/{model:path}")  # 走bfl接口透传
async def create_async_task(
        request: Request,
        model: str,  # response_model 计费模型

        headers: dict = Depends(get_headers),
        # api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(bjson(headers))

    try:
        payload = await request.json()
    except Exception as e:
        payload = (await request.form())._dict
        payload = payload or (await request.body()).decode()

    # payload['polling_url'] = "TODO"
    return payload


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

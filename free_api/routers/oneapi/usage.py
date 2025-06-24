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


@router.post("/v1/{dynamic_router:path}")  # 按量计费
async def create_chat_completions(
        dynamic_router: str,
        request: dict,  # 有些参数传不进 oneapi 用替代方案
):
    usage = request.get('metadata') or request.get('extra_fields')
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


@router.api_route("/async/flux/v1/{model:path}", methods=["GET", "POST"])  # 走bfl接口透传
async def create_async_task(
        request: Request,
        model: str,  # response_model

        # headers: dict = Depends(get_headers),
        # api_key: Optional[str] = Depends(get_bearer_token),
):
    """
            TaskStatusNotStart              = "NOT_START"
            TaskStatusSubmitted             = "SUBMITTED"
            TaskStatusQueued                = "QUEUED"
            TaskStatusInProgress            = "IN_PROGRESS"
            TaskStatusFailure               = "FAILURE"  # todo: 补偿积分+状态记录
            TaskStatusSuccess               = "SUCCESS"
            TaskStatusUnknown               = "UNKNOWN
    """
    params = request.query_params._dict  # 进不去内部的 只有id可以进
    task_id = params.get('id') or params.get('task_id') or params.get('request_id')
    if request.method == 'GET':
        return {
            "id": task_id,
            "result": {},
            "status": np.random.choice(["IN_PROGRESS", "FAILURE", "SUCCESS", "Ready"]),

            "response_model": model,  # 计费模型
            "error": "展示错误"
        }

    try:
        payload = await request.json()
    except Exception as e:
        payload = (await request.form())._dict
        payload = payload or (await request.body()).decode()

    payload['response_model'] = model  # 计费模型
    return payload


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

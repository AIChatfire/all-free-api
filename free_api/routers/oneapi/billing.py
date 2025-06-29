#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : billing
# @Time         : 2025/6/24 08:59
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import json

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.apis.utils import make_request
from meutils.db.redis_db import redis_aclient

from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from meutils.schemas.openai_types import CompletionRequest, chat_completion, chat_completion_chunk, \
    chat_completion_chunk_stop

from meutils.schemas.image_types import ImageRequest, ImagesResponse

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["bling"]


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


# 渠道错乱会导致失败，可删除重建
@router.api_route("/async/flux/v1/{model:path}", methods=["GET", "POST"])  # 走bfl接口透传
async def create_async_task_for_billing(
        request: Request,
        model: str,  # response_model 计费模型

        id: str = Query(None, description="The ID of the task."),  # local task id

        headers: dict = Depends(get_headers),
        # api_key: Optional[str] = Depends(get_bearer_token),
):
    """传递状态 https://docs.bfl.ai/api-reference/utility/get-result

    """
    logger.debug(bjson(headers))

    if request.method == "GET":

        if response := await redis_aclient.get(f"response:{id}"):
            response = json.loads(response)
            return response

        # 测试
        if flux := await redis_aclient.get("flux"):
            data = json.loads(flux)
            return {
                "id": id,
                "result": {},
                **data
            }

        return {
            "id": id,
            "result": {},
            "status": "Processing",
        }

    """
    {
        "id": "fddbade0-a2f7-4082-981a-961616870906",
        "status": "Task not found",
        "result": null,
        "progress": null,
        "details": null
        }
    """

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

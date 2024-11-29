#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chatfire_provider
# @Time         : 2024/8/30 13:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from aiostream import stream

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, appu
from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS
from meutils.config_utils.lark_utils import get_next_token_for_polling

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Path

from meutils.apis.textcard import hanyuxinjie

router = APIRouter()
TAGS = ["文本生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        model: str = Query("Pro/THUDM/glm-4-9b-chat"),
        title: str = Query("🔥汉语新解"),
        auth: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth

    if '/' in request.model:  # 替换内置模型
        model = request.model

    response = hanyuxinjie.create(request.last_content, model, title)
    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response))

    if hasattr(response, "model"):
        response.model = model  # 以请求体为主

    response = await stream.list(response)
    return create_chat_completion(response)


# @router.get("/") # html
# async def create_chat_completions(
#         request: ChatCompletionRequest,
#         auth: Optional[str] = Depends(get_bearer_token),
# ):
#     logger.debug(request.model_dump_json(indent=4))
#
#     api_key = auth
#
#     model = "汉语新解"
#     await appu(model, api_key)
#
#     response = hanyuxinjie.create(request.last_content, request.model)
#     if request.stream:
#         return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=model))
#
#     if hasattr(response, "model"):
#         response.model = model  # 以请求体为主
#     return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

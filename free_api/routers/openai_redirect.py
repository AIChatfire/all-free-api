#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chatfire_provider
# @Time         : 2024/8/30 13:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions.redirect import Completions

router = APIRouter()
TAGS = ["文本生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/{model}/to/{redirect_model}/v1/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        model: str = 'gpt-3.5-turbo',
        redirect_model: str = 'deepseek-chat',  # 默认
        redirect_base_url: Optional[str] = Query('https://api.chatfire.cn/v1'),

        threshold: Optional[int] = None,
        # threshold: Optional[int] = Query(1000),

):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None

    request.model = model
    if threshold is None or len(str(request.messages)) > threshold:  # 动态切模型: 默认切换模型，可设置大于1000才切换
        request.model = redirect_model

    data = to_openai_completion_params(request)
    response = await AsyncClient(api_key=api_key, base_url=redirect_base_url).chat.completions.create(**data)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=model))

    if hasattr(response, "model"):
        response.model = model  # 以请求体为主
    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

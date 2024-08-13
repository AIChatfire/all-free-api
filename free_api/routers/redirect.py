#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : polling_openai_api_keys
# @Time         : 2024/6/17 17:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions.redirect import Completions

router = APIRouter()
TAGS = ["文本生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        # auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        model: Optional[str] = Query('ep-20240515073524-xj4m2'),
        base_url: Optional[str] = Query('https://ark.cn-beijing.volces.com/api/v3'),
        api_key: Optional[str] = Query(None),

        redirect_model: Optional[str] = Query('deepseek-chat'),
        redirect_base_url: Optional[str] = Query('https://api.deepseek.com/v1'),
        redirect_api_key: Optional[str] = Query(None),

        threshold: Optional[int] = Query(32000),

):
    # api_key = auth and auth.credentials or None
    logger.debug(request.model_dump_json(indent=4))

    raw_model   = request.model

    client = Completions(
        model,
        base_url,
        api_key,

        redirect_model,
        redirect_base_url,
        redirect_api_key,

        threshold=threshold
    )

    response = await client.create(request)
    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=raw_model))

    if hasattr(response, "model"):
        response.model = raw_model  # 以请求体为主

    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

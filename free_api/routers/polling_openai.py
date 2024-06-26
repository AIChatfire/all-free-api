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
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.oneapi_types import REDIRECT_MODEL

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.controllers.completions.polling_openai import Completions

router = APIRouter()

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        base_url: Optional[str] = Query(),
        feishu_url: Optional[str] = Query(None),
        redis_key: Optional[str] = Query(None),
):
    logger.debug(request)
    logger.debug(base_url)
    logger.debug(feishu_url)

    raw_model = request.model
    if any(i in base_url for i in {"xinghuo", "siliconflow", "lingyiwanwu"}):  # 实际调用
        request.model = REDIRECT_MODEL.get(request.model, request.model)

    api_key = auth and auth.credentials or None

    client = Completions(api_key=api_key, base_url=base_url, feishu_url=feishu_url, redis_key=redis_key)

    response = await client.acreate(request)

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

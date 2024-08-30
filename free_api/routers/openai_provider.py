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


@router.post("/{model}/v1/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        model: str = 'kimi',

):
    request.model = model
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None

    response = await AsyncClient().chat.completions.create(**to_openai_completion_params(request))

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response))

    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

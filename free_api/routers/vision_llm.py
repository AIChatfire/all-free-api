#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : vision_llm
# @Time         : 2024/8/20 13:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion_chunk, create_chat_completion
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions.vision_llm import Completions

router = APIRouter()
TAGS = ["VISION"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[str] = Depends(get_bearer_token),
):
    api_key = auth
    logger.debug(request.model_dump_json(indent=4))

    raw_model = request.model

    response = await Completions().create(request)

    logger.debug(response)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=raw_model))
    else:
        return create_chat_completion(response, redirect_model=raw_model)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

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
from meutils.schemas.openai_types import chat_completion

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions.chatfire_all import Completions

router = APIRouter()

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        system_prompt: Optional[str] = Query(None)
):
    api_key = auth and auth.credentials or None
    logger.debug(request.model_dump_json(indent=4))

    raw_model = request.model
    if request.model.endswith("-all"):
        request.model = 'glm-4-alltools'
        request.tools = TOOLS  # 开启工具：目前支持3个
        if system_prompt:  # 定制化模型
            request.messages = [{"role": "system", "content": system_prompt}] + request.messages

    client = Completions(api_key=api_key)
    if request.stream:
        response = await client.create(request)
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=raw_model))
    else:
        return chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_adapter
# @Time         : 2024/8/7 12:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from aiostream import stream

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_completion_params
from meutils.llm.completions.rag import fire as rag_fire

from meutils.schemas.openai_types import ChatCompletionRequest

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["智能体"]


@router.post("/{agent}/{model}/{path:path}")
async def create_chat_completions(
        request: ChatCompletionRequest,

        path: str = "v1/chat/completions",  # 兼容性
        agent: str = "rag",  # 代理
        model: str = 'qwen-turbo-2024-11-01',  # 1M

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    request.model = model

    response = None
    if agent == "rag":  # 适配o1
        if request.stream:
            request.stream_options = {"include_usage": True}
        response = await rag_fire.Completions().create(request)

    #########################################################################################################
    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=model))

    if inspect.isasyncgen(response):  # 非流：将流转换为非流
        logger.debug("IS_ASYNC_GEN")

        chunks = await stream.list(response)
        response = create_chat_completion(chunks)

        # logger.debug(response)

        prompt_tokens = int(len(str(request.messages)) // 1.25)
        completion_tokens = int(len(''.join(chunks)) // 1.25)

        if hasattr(response.usage, "prompt_tokens"):
            response.usage.prompt_tokens = response.usage.prompt_tokens or prompt_tokens
            response.usage.completion_tokens = response.usage.completion_tokens or completion_tokens
        else:
            response.usage['prompt_tokens'] = prompt_tokens
            response.usage['completion_tokens'] = completion_tokens

    if hasattr(response, "model"):
        response.model = model  # 以请求体为主
    return response  # chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_rag
# @Time         : 2024/11/21 16:50
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 单文件


from aiostream import stream

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_params
from meutils.llm.completions import chat_plus
from meutils.apis.search import web_search

from meutils.schemas.openai_types import CompletionRequest

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["文本生成"]


@router.post("/{redirect_model:path}")  # todo: 映射函数
async def create_chat_completions(
        request: CompletionRequest,

        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4, exclude_none=True))

    raw_model = request.model

    # response = web_search.Completions(api_key=api_key).create(request)

    response = await chat_plus.Completions(api_key=api_key).create(request)

    #########################################################################################################
    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=raw_model))

    if inspect.isasyncgen(response):  # 非流：将流转换为非流 tdoo 計算tokens
        logger.debug("IS_ASYNC_GEN")

        chunks = await stream.list(response)
        response = create_chat_completion(chunks)

        # logger.debug(response)

        prompt_tokens = int(len(str(request.messages)) // 2)
        completion_tokens = int(len(''.join(chunks)) // 2)

        if hasattr(response.usage, "prompt_tokens"):
            response.usage.prompt_tokens = prompt_tokens
            response.usage.completion_tokens = completion_tokens
            response.usage.total_tokens = prompt_tokens + completion_tokens
        else:
            response.usage['prompt_tokens'] = prompt_tokens
            response.usage['completion_tokens'] = completion_tokens
            response.usage['total_tokens'] = prompt_tokens + completion_tokens

    if hasattr(response, "model"):
        response.model = raw_model  # 以请求体为主
    return response  # chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")

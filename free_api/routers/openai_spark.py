#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_adapter
# @Time         : 2024/8/7 12:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 适配功能： file video image audio 等等

from aiostream import stream

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_params
from meutils.llm.completions.rag import fire as rag_fire
from meutils.schemas.openai_types import ChatCompletionRequest

from openai import OpenAI, AsyncOpenAI
from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["适配SparkAI"]


@router.post("/{path:path}")
async def create_chat_completions(
        request: ChatCompletionRequest,

        path: str = "v1/chat/completions",  # 兼容性
        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))

    if request.urls and "image_url" in str(request.messages):
        request.messages[-1]['content'] = [{"type": "image_url", "image_url": {"url": request.urls[-1]}}]

        data = to_openai_params(request)
        response = await AsyncOpenAI(api_key=api_key).chat.completions.create(**data)

    else:
        response = await rag_fire.Completions(api_key=api_key).create(request)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response))

    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")
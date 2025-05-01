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
from meutils.decorators.contextmanagers import atry_catch

from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_params
from meutils.llm.completions import chat_spark

from meutils.schemas.openai_types import CompletionRequest
from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["SparkAI"]


@router.post("/{path:path}")
async def create_chat_completions(
        request: CompletionRequest,

        path: str = "v1/chat/completions",  # 兼容性

        api_key: Optional[str] = Depends(get_bearer_token),
):
    async with atry_catch(f"{path}", api_key=api_key, request=request):
        response = await chat_spark.Completions(api_key=api_key).create(request)

        if request.stream:
            return EventSourceResponse(create_chat_completion_chunk(response))

        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

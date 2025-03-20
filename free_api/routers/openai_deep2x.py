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
from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_params
from meutils.llm.completions import deep2x

from meutils.schemas.openai_types import CompletionRequest

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Header, Query, Form, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["deep2x"]


@router.post("/{path:path}")  # 兼容openai, 其他参数放路径或者headers
async def create_chat_completions(
        request: CompletionRequest,

        api_key: Optional[str] = Depends(get_bearer_token),

        # reasoning_stream: bool = Header(False),

):
    logger.debug(request.model_dump_json(indent=4))

    redirect_model = f"deep-{request.model.split('-', )[0]}"

    response = deep2x.Completions(api_key=api_key).create(request)

    # logger.debug(response)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=redirect_model))

    else:
        response = (await stream.list(response))[0]
        if hasattr(response, "model"):
            response.model = redirect_model
        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

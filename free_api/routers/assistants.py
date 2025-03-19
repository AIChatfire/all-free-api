#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : assistants
# @Time         : 2025/3/18 19:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, to_openai_params
from meutils.llm.completions import chat_spark

from meutils.llm.clients import zhipuai_sdk_client
from meutils.caches import cache

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["assistants"]


@router.get("/assistants")
@cache(ttl=24 * 3600)
async def create_chat_completions(
        # api_key: Optional[str] = Depends(get_bearer_token), # 不鉴权
):
    return zhipuai_sdk_client.assistant.query_support()


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

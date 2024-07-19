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

from free_api.resources.completions.polling_openai import Completions

router = APIRouter()

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@alru_cache(ttl=10)
async def get_token():
    await asyncio.sleep(3)
    logger.debug(f"没走缓存 {time.time()}")

    return time.time()


@router.get("/chat/completions")
async def create_chat_completions(
        # request: ChatCompletionRequest,
        # auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    return await get_token()


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

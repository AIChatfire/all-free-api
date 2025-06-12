#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : transparent
# @Time         : 2025/6/12 11:56
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 透传 tokens计费
"""
Request transparent transmission
"""

from meutils.pipe import *
from meutils.decorators.contextmanagers import atry_catch

from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.llm.openai_polling.chat import Completions
from meutils.llm.openai_polling.images import Images

from meutils.schemas.openai_types import CompletionRequest
from meutils.schemas.image_types import ImageRequest, ImagesResponse

from meutils.serving.fastapi.dependencies import get_headers, get_bearer_token

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["tokens计费"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/billing/v1/chat/completions")  # todo: 动态
async def create_chat_completions(

        request: CompletionRequest,

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

         request_model: Optional[str] = Query(None),  # 优先级最高
        response_model: Optional[str] = Query(None),  # 兼容newapi自定义接口 ?response_model=""

):


    # https://all.chatfire.cc/g/openai
    base_url = headers.get("base-url") or headers.get("x-base-url") or "https://api.siliconflow.cn/v1"  # newapi里需反代

    response_model = response_model or request.model
    async with atry_catch(f"{base_url}/{path}", api_key=api_key, headers=headers, request=request):
        ###########################################################################
        # 重定向：deepseek-chat==deepseek-v3 展示key 调用value

        if request_model:
            request.model = request_model

        if "==" in request.model:
            response_model, request_model = request.model.split("==", maxsplit=1)
            request.model = request_model

        ###########################################################################

        client = Completions(base_url=base_url, api_key=api_key, http_client=http_client)
        response = await client.create(request)

        # exceeds the maximum
        # System is too busy now. Please try again later.
        # 400 {"code":20015,"message":"length of prompt_tokens (235121) must be less than max_seq_len (65536).","data":null}

        if request.stream:
            return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=response_model))

        if hasattr(response, "model"):
            response.model = response_model

        return response

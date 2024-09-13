#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_adapter
# @Time         : 2024/8/7 12:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion_chunk, to_openai_completion_params
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS
from meutils.llm.completions import dify, tryblend

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions import sensechat, chat_qianfan

router = APIRouter()
TAGS = ["文本生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        threshold: Optional[int] = Query(None),
        max_turns: Optional[int] = None,

        vip: Optional[bool] = Query(False),

):
    api_key = auth and auth.credentials or None
    logger.debug(request.model_dump_json(indent=4))

    raw_model = request.model

    if max_turns:  # 限制对话轮次
        request.messages = request.messages[-(2 * max_turns - 1):]

    response = None
    if request.model.lower().startswith(("o1",)):
        if "RESPOND ONLY WITH THE TITLE TEXT" in str(request.last_content): return

        data = to_openai_completion_params(request)
        data['stream'] = False
        data.pop('max_tokens', None)
        response = await AsyncClient(api_key=api_key, timeout=100).chat.completions.create(**data)  # 定向渠道
        if request.stream:
            response = response.choices[0].message.content

    elif request.model.lower().startswith(("sensechat",)):
        client = sensechat.Completions(threshold=threshold)
        response = await client.create(request)

    elif request.model.lower().startswith(("ernie",)):
        client = chat_qianfan.Completions(threshold=threshold)
        response = await client.create(request)

    elif api_key.startswith(("app-",)):  # 适配dify
        client = dify.Completions(api_key=api_key)
        response = client.create(request)  # List[str]

    elif api_key.startswith(("tryblend",)):  # 目前仅适配流式
        client = tryblend.Completions(vip=vip)
        response = await client.create(request)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=raw_model))

    if hasattr(response, "model"):
        response.model = raw_model  # 以请求体为主

    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

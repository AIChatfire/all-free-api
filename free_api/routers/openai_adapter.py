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
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS
from meutils.llm.completions import dify, tryblend, tune, delilegal
from meutils.config_utils.lark_utils import get_next_token_for_polling

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions import sensechat, chat_qianfan, yuanbao  # todo

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
    if request.model.lower().startswith(("o1", "openai/o1")) and not api_key.startswith('tune'):  # 适配o1
        if "RESPOND ONLY WITH THE TITLE TEXT" in str(request.last_content): return

        base_url = None
        if api_key.startswith('sk-tune'):  # https://studio.tune.app/playground
            request.model = f"openai/{request.model}"
            base_url = 'https://any2chat.chatfire.cn/tune/v1'
            api_key = await get_next_token_for_polling(tune.FEISHU_URL_API)

        request.model = request.model.strip('-all')
        request.messages = [message for message in request.messages if message['role'] != 'system']

        data = to_openai_completion_params(request)
        data['stream'] = False
        data.pop('max_tokens', None)
        response = await AsyncClient(api_key=api_key, base_url=base_url, timeout=100).chat.completions.create(**data)
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

    elif api_key.startswith(("tryblend",)):
        client = tryblend.Completions(vip=vip)
        response = await client.create(request)

    elif api_key.startswith(("deli",)):  # 逆向
        response = delilegal.create(request)

    elif api_key.startswith(("tune",)):  # 逆向
        response = tune.create(request, vip=vip)

    elif api_key.startswith(("sk-tune",)):
        if request.model.startswith("claude-3-5-sonnet"):
            request.model = "anthropic/claude-3.5-sonnet"
            request.max_tokens = request.max_tokens or 8192  # c35必须有max_tokens 8192

        data = to_openai_completion_params(request)
        base_url = 'https://any2chat.chatfire.cn/tune/v1'
        api_key = await get_next_token_for_polling(tune.FEISHU_URL_API)
        response = await AsyncClient(api_key=api_key, base_url=base_url, timeout=100).chat.completions.create(**data)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=raw_model))

    if inspect.isasyncgen(response):
        chunks = await stream.list(response)
        response = create_chat_completion(chunks)

        response.usage.prompt_tokens = int(len(str(request.messages)) // 1.25)
        response.usage.completion_tokens = int(len(''.join(chunks)) // 1.25)

    if hasattr(response, "model"):
        response.model = raw_model  # 以请求体为主
    return response  # chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")

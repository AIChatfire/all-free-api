#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chatfire_provider
# @Time         : 2024/8/30 13:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS
from meutils.config_utils.lark_utils import get_next_token_for_polling

from openai import AsyncClient
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Path

from free_api.resources.completions.redirect import Completions

router = APIRouter()
TAGS = ["文本生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/{model:path}/to/{redirect_model:path}/v1/chat/completions")  # {model:path} {redirect_model:path}
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        model: str = 'gpt-3.5-turbo',
        redirect_model: str = "deepseek-chat",  # 默认
        redirect_base_url: Optional[str] = Query('https://api.chatfire.cn/v1'),

        threshold: Optional[int] = None,
        max_turns: Optional[int] = None,
):
    logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None
    if api_key.startswith('http'):
        api_key = await get_next_token_for_polling(feishu_url=api_key)  # 飞书轮询

    if max_turns:  # 限制对话轮次
        request.messages = request.messages[-(2 * max_turns - 1):]

    request.model = model
    if (threshold is None
            or len(str(request.messages)) > threshold  # 动态切模型: 默认切换模型，可设置大于1000才切换
            or "RESPOND ONLY WITH THE TITLE TEXT" in str(request.last_content)
    ):
        request.model = redirect_model
        openai = AsyncClient(api_key=api_key[:51], base_url=redirect_base_url)  # 避免指定渠道
    else:
        openai = AsyncClient(api_key=api_key)

    data = to_openai_completion_params(request)
    response = await openai.chat.completions.create(**data)
    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=model))

    if hasattr(response, "model"):
        response.model = model  # 以请求体为主
    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

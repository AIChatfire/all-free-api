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

router = APIRouter()
TAGS = ["重定向"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/{model:path}/to/{redirect_model:path}")  # {model:path} {redirect_model:path}
async def create_chat_completions(
        request: ChatCompletionRequest,

        model: str = 'gpt-3.5-turbo',  # 源模型

        # 兜底模型
        redirect_model: str = "deepseek-chat",  # 目标模型 支持lambda "lambda m: m.split('-')[0]"
        redirect_base_url: Optional[str] = Query('https://api.chatfire.cn/v1'),  # 目标地址 => base_url

        threshold: Optional[int] = None,
        max_turns: Optional[int] = None,

        api_key: Optional[str] = Depends(get_bearer_token),  # 渠道密钥
):
    logger.debug(request.model_dump_json(indent=4))

    # 渠道密钥
    if api_key.startswith('http'):  # 飞书轮询
        api_key = await get_next_token_for_polling(feishu_url=api_key)
    elif ',' in api_key:  # 字符串：todo redis
        api_key = np.random.choice(api_key.split(','))

    if max_turns:  # 限制对话轮次
        request.messages = request.messages[-(2 * max_turns - 1):]

    if (threshold is None
            or len(str(request.messages)) > threshold  # 动态切模型: 默认切换模型，可设置大于1000才切换
            or "RESPOND ONLY WITH THE TITLE TEXT" in str(request.last_content)
    ):
        request.model = redirect_model if 'lambda' not in redirect_model else eval(redirect_model)(model)  # 模型映射
        openai = AsyncClient(api_key=api_key, base_url=redirect_base_url)
    else:
        request.model = model
        openai = AsyncClient()

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

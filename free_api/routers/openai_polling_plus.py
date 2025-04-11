#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : polling_openai_api_keys
# @Time         : 2024/6/17 17:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import typing

from meutils.pipe import *
from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.llm.openai_polling.chat import Completions
from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.schemas.openai_types import CompletionRequest
from meutils.serving.fastapi.dependencies import get_headers, get_bearer_token

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["轮询"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]

"""
1. 多账号轮询
2. redis/string
3. 自动剔除账号
4. 支持任意任务：不仅仅是chat
5. 支持重定向
6. 支持流转非流、非流转流
7. 计算tokens

“{model}::{redirect_model}”
"""


@router.post("/{path:path}")
async def create_chat_completions(
        path: str,  # "chat/completions"

        request: CompletionRequest,

        headers: dict = Depends(get_headers),
        api_key: Optional[str] = Depends(get_bearer_token),

):
    logger.debug(request.model_dump_json(exclude_none=True, indent=4))

    with try_catch(f"{__name__}: {path}", api_key=api_key, headers=headers, request=request):

        # https://all.chatfire.cc/g/openai
        base_url = headers.get("base_url") or "https://api.siliconflow.cn/v1"

        if path.endswith("images/generations"):
            pass

        else:  # chat/completions 默认聊天

            # 重定向：deepseek-chat:deepseek-v3 展示key 调用value
            model = request.model
            if ":" in request.model:
                model, redirect_model = request.model.split(":", maxsplit=1)
                request.model = redirect_model

            client = Completions(api_key=api_key, base_url=base_url)
            response = await client.create(request)

            if request.stream:
                return EventSourceResponse(create_chat_completion_chunk(response, redirect_model=model))

            if hasattr(response, "model"):
                response.model = model  # response_model

            return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

"""


curl -X 'POST' \
  'http://0.0.0.0:8000/v1/xx' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer redis:https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=rWMtht' \
  -H 'base_url: https://all.chatfire.cc/g/openai' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "讲个故事",
      "role": "user"
    }
  ],
  "model": "xxxxxxxx:gemini-2.0-flash",
  "stream": true
}'

"""

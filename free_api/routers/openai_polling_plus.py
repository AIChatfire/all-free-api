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
from meutils.schemas.openai_types import ChatCompletionRequest, TOOLS
from meutils.schemas.oneapi import REDIRECT_MODEL

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

from free_api.resources.completions.polling_openai import Completions

router = APIRouter()
TAGS = ["文本生成", "轮询"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]

"""
1. 多账号轮询
2. redis/string
3. 自动剔除账号
4. 支持任意任务：不仅仅是chat
5. 支持重定向
6. 支持流转非流、非流转流
7. 计算tokens

“{model}:{redirect_model}”
"""


@router.post("/{openai_path:path}")
async def create_chat_completions(
        request: ChatCompletionRequest,
        base_url: Optional[str] = Query("https://api.siliconflow.cn/v1"),
        feishu_url: Optional[str] = Query(None),
        redis_key: Optional[str] = Query(None),

        openai_path: Optional[str] = "chat/completions",

        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))
    # logger.debug(base_url)
    # logger.debug(feishu_url)

    raw_model = request.model
    if any(i in base_url for i in {"spark-api", "siliconflow", "together", "lingyiwanwu"}):  # 实际调用
        if request.model.startswith("gemini-1.5"):
            request.model = REDIRECT_MODEL.get("gemini-1.5")
        else:  # https://spark-api-open.xf-yun.com/v1
            request.model = REDIRECT_MODEL.get(request.model, request.model)

    client = Completions(api_key=api_key, base_url=base_url, feishu_url=feishu_url, redis_key=redis_key)
    response = await client.acreate(request)

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

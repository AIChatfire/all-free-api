#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : completions
# @Time         : 2023/12/19 16:38
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 逆向工程

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status
from sse_starlette import EventSourceResponse

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from free_api.resources.completions.step import Completions
from meutils.schemas.openai_types import ChatCompletionRequest

router = APIRouter()

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        base_url: Optional[str] = Query(None),
):
    logger.debug(request)
    logger.debug(base_url)

    api_key = auth and auth.credentials or None
    api_key = np.random.choice(api_key.strip().split(','))  # 随机轮询

    response = await Completions(api_key=api_key).acreate(request)

    if request.stream:
        return EventSourceResponse(response)
    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_video
# @Time         : 2024/7/25 10:59
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.schemas.openai_types import CompletionRequest
from meutils.llm.completions.chat_videos import Completions

from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk

router = APIRouter()
TAGS = ["VIDEOS"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: CompletionRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))

    if request.stream:

        response = Completions(api_key).create(request)

        return EventSourceResponse(create_chat_completion_chunk(response))
    else:
        return chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

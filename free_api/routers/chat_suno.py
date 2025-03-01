#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_suno
# @Time         : 2024/6/25 09:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk
from meutils.schemas.openai_types import ChatCompletionRequest

from fastapi import APIRouter, Depends, BackgroundTasks
from sse_starlette import EventSourceResponse

from free_api.resources.completions.suno import Completions

router = APIRouter()
TAGS = ["SunoAI"]


@router.post('/chat/completions')
async def generate_music_for_chat(
        request: ChatCompletionRequest,
        api_key: Optional[str] = Depends(get_bearer_token),

        backgroundtasks: BackgroundTasks = BackgroundTasks,
):

    chunks = await Completions(api_key=api_key).create(request)

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(chunks))

    return create_chat_completion("suno模型请切换为stream")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

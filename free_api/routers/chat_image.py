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
from meutils.schemas.openai_types import ChatCompletionRequest, ImageRequest
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

router = APIRouter()
TAGS = ["文本生成", "文生图"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = ...,
):
    logger.debug(request)
    image_request = ImageRequest(
        prompt=request.last_content,
        model=request.model.strip('chat-'),
        n=2,
    )

    api_key = auth and auth.credentials or None

    response = await AsyncOpenAI(api_key=api_key).images.generate(**image_request.model_dump())

    if request.stream:
        async def gen():
            for image in response.data:
                yield f"![{image.revised_prompt}]({image.url})"

        chunks = create_chat_completion_chunk(gen())
        return EventSourceResponse(chunks)
    else:
        chat_completion.choices[0].message.content = response
        return create_chat_completion(chat_completion)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

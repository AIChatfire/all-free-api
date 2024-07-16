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
from meutils.llm.openai_utils import to_openai_images_params, to_openai_completion_params

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

router = APIRouter()
TAGS = ["多模型问答"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]

examples = [
    {
        "model": "chat-kolors",
        "messages": [
            {
                "role": "user",
                "content": "@deepseek-chat@deepseek-coder 1+1"
            }
        ],
        "stream": True
    }
]


@router.post("/chat/completions")  # todo: chat models
async def create_chat_completions(
        request: ChatCompletionRequest = Body(examples=examples),
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks(),
):
    logger.debug(request)
    api_key = auth and auth.credentials or None

    models = re.findall(r'@([\w-]+)', request.last_content)
    logger.debug(models)

    request.model = models[0] if models else 'deepseek-chat'  # 默认模型

    for message in request.messages:
        if message['role'] == 'user':
            message['content'] = re.sub(r'@([\w-]+)', '', message['content'])

    logger.debug(request)

    data = to_openai_completion_params(request)

    task = AsyncOpenAI(api_key=api_key).chat.completions.create(**data)

    future_tasks = []
    for model in models:
        request.model = model
        request.stream = False
        data = to_openai_completion_params(request)
        future_tasks.append(AsyncOpenAI(api_key=api_key).chat.completions.create(**data))

    if request.stream:
        # response = await AsyncOpenAI(api_key=api_key).chat.completions.create(**data)
        chunks = await task

        # chunks = achain()

        chunks = create_chat_completion_chunk(chunks)
        return EventSourceResponse(chunks)
    else:

        chat_completion.choices[0].message.content = 'todo：非流失'
        return create_chat_completion(chat_completion)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

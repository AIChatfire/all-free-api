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
from meutils.llm.openai_utils import to_openai_images_params

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

router = APIRouter()
TAGS = ["文本生成", "文生图"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]

#
# @router.post("/chat/completions")
# async def create_chat_completions(
#         request: ChatCompletionRequest, # request: ChatCompletionRequest = Body(examples=[])
#         auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
#         backgroundtasks: BackgroundTasks = BackgroundTasks(),
# ):
#     logger.debug(request)
#
#     image_request = ImageRequest(
#         prompt=request.last_content,
#         model=request.model.strip('chat-'),
#         n=2 if "dall-e-3" not in request.model else 1,  # dall-e-3 仅支持 1
#     )
#
#     data = to_openai_images_params(image_request)
#
#     api_key = auth and auth.credentials or None
#     response = await AsyncOpenAI(api_key=api_key).images.generate(**data)
#
#     if request.stream:
#         async def gen():
#             for image in response.data:
#                 yield f"![{image.revised_prompt}]({image.url})\n\n"
#
#         chunks = create_chat_completion_chunk(gen())
#         return EventSourceResponse(chunks)
#     else:
#         chat_completion.choices[0].message.content = response
#         return create_chat_completion(chat_completion)

examples = [
    {
        "model": "chat-kolors",
        "messages": [
            {
                "role": "user",
                "content": "一只可爱的边牧在坐公交车，卡通贴纸。动漫3D风格，超写实油画，超高分辨率，最好的质量，8k"
            }
        ],
        "stream": True
    }
]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest = Body(examples=examples),
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks(),
):
    logger.debug(request)

    image_request = ImageRequest(
        prompt=request.last_content,
        model=request.model.strip('chat-'),
        n=2 if "dall-e-3" not in request.model else 1,  # dall-e-3 仅支持 1
    )

    data = to_openai_images_params(image_request)

    api_key = auth and auth.credentials or None

    future_task = asyncio.create_task(AsyncOpenAI(api_key=api_key).images.generate(**data))  # 异步执行
    if request.stream:
        async def gen():
            for i in f"> 🖌️正在绘画\n\n```json\n{image_request.model_dump()}\n\n```\n\n":
                await asyncio.sleep(0.05)
                yield i

            response = await future_task
            for image in response.data:
                yield f"![{image.revised_prompt}]({image.url})\n\n"

        chunks = create_chat_completion_chunk(gen())
        return EventSourceResponse(chunks)
    else:
        response = await future_task

        chat_completion.choices[0].message.content = response
        return create_chat_completion(chat_completion)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

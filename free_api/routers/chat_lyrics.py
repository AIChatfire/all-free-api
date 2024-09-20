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
from meutils.apis.sunoai import suno

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.schemas.openai_types import ChatCompletionRequest, ImageRequest
from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion
from meutils.llm.openai_utils import to_openai_images_params

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk

router = APIRouter()
TAGS = ["SunoAI"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]

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
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    logger.debug(request.model_dump_json(indent=4))
    api_key = auth and auth.credentials or None

    prompt = request.last_content
    _ = {"prompt": prompt}

    future_task = asyncio.create_task(suno.generate_lyrics(prompt=prompt))  # 异步执行
    if request.stream:
        async def gen():
            for i in f"""> 正在生成\n\n```json\n{_}\n```\n\n""":
                await asyncio.sleep(0.2)
                yield i

            data = await future_task
            title = data.get("title")
            text = data.get("text")

            yield f"# {title}\n\n"
            yield f"```text\n{text}\n```"

        chunks = create_chat_completion_chunk(gen())
        return EventSourceResponse(chunks)
    else:
        data = await future_task

        chat_completion.choices[0].message.content = data
        return chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

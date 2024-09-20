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
from meutils.schemas.runwayml_types import RunwayRequest, Options
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.task_types import Task

from meutils.llm.openai_utils import create_chat_completion, create_chat_completion_chunk, chat_completion

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body
from sse_starlette import EventSourceResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from free_api.resources.completions.chat_video import Completions

router = APIRouter()
TAGS = ["VIDEO"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    if isinstance(request.last_content, str) and request.last_content.startswith(  # 跳过nextchat
            (
                    "hi",
                    "使用四到五个字直接返回这句话的简要主题",
                    "简要总结一下对话内容，用作后续的上下文提示 prompt，控制在 200 字以内")):
        return

    if request.stream:

        chunks = await Completions(api_key).create(request)
        chunks = create_chat_completion_chunk(chunks)

        return EventSourceResponse(chunks)
    else:
        return chat_completion


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
    # for i in range(10):
    #     send_message(f"兜底模型", title="github_copilot")

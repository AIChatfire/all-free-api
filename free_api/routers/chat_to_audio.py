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
from meutils.llm.openai_utils import create_chat_completion_chunk, to_openai_completion_params
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.oss.minio_oss import Minio

from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai import AsyncOpenAI

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Header

router = APIRouter()
TAGS = ["文本生成", "语音生成"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/chat/completions")
async def create_chat_completions(
        request: ChatCompletionRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        tts_model: str = Query("tts-1"),
        is_html: bool = Query(False)

):
    api_key = auth and auth.credentials or None

    data = to_openai_completion_params(request)
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(**data)

    async def gen():
        content = ""
        async for chunk in response:
            _ = chunk.choices[0].delta.content or ""
            content += _
            yield _

        # tts
        stream = await client.audio.speech.create(input=content, model=tts_model, voice="alloy")

        bucket_name = "files"
        file = UploadFile(
            file=io.BytesIO(stream.content),
            filename=f"{shortuuid.random()}.mp3",
            size=1,
        )
        file_object = await Minio().put_object_for_openai(file=file, bucket_name=bucket_name)

        url = file_object.filename
        audio = f"\n\n[🎧音频-点击播放]({url})"
        if is_html:
            audio = f"""\n\n
            <video src="{url}" controls="controls" muted="muted" class="d-block rounded-bottom-2 border-top" width="100%" height="50"></video>
            """
        yield audio

    if request.stream:
        return EventSourceResponse(create_chat_completion_chunk(gen()))
    else:
        return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

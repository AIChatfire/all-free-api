#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : speech
# @Time         : 2023/12/26 14:12
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.ai_audio.tts import EdgeTTS
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from chatllm.schemas.openai_types import SpeechCreateRequest  #

router = APIRouter()
TAGS = ["audio"]


@router.post("/audio/speech")
async def create_speech(
        request: SpeechCreateRequest,
        voice: Optional[str] = Query(None),
):
    logger.debug(request)

    # media_types = {
    #     "mp3": "audio/mpeg",
    #     "opus": "audio/opus",
    #     "aac": "audio/aac",
    #     "flac": "audio/flac",
    #     "wav": "audio/wav",
    #     "pcm": "text/event-stream",
    # }
    # media_types.get(request.response_format)

    data = request.model_dump()
    data["voice"] = voice or data["voice"]  # 支持很多种声音

    stream = await EdgeTTS().acreate_for_openai(**data)

    return StreamingResponse(stream, media_type="text/event-stream")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

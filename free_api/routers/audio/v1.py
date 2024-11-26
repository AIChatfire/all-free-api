#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : speech
# @Time         : 2023/12/26 14:12
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo: fish 多种音色支持

from meutils.pipe import *
from meutils.io.files_utils import to_bytes
from meutils.schemas.openai_types import TTSRequest, STTRequest

from meutils.llm.openai_utils import ppu_flow
from meutils.ai_audio.tts import EdgeTTS
from meutils.apis.siliconflow import audio as siliconflow_audio
from meutils.apis.audio import deepinfra as deepinfra_audio

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status, Response
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()
TAGS = ["Audio"]


@router.post("/audio/speech")
async def create_speech(
        request: TTSRequest,

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        n: Optional[int] = Query(1),  # 默认收费
):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    # media_types = {
    #     "mp3": "audio/mpeg",
    #     "opus": "audio/opus",
    #     "aac": "audio/aac",
    #     "flac": "audio/flac",
    #     "wav": "audio/wav",
    #     "pcm": "text/event-stream",
    # }
    # media_types.get(request.response_format)
    media_type = "application/octet-stream"

    data = request.model_dump()

    async with ppu_flow(api_key, post='api-tts', n=n):
        stream = await EdgeTTS().acreate_for_openai(**data)  # todo 优化

        # text/event-stream => application/octet-stream
        return StreamingResponse(stream, media_type=media_type)


@router.post("/audio/transcriptions")
async def create_transcriptions(
        file: Optional[Union[str, UploadFile]] = File(...),
        model: str = Form("whisper-1"),
        language: Optional[str] = Form(None),
        prompt: Optional[str] = Form(None),
        response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] = Form("text"),
        temperature: Optional[float] = Form(None),
        timestamp_granularities: Optional[List[Literal["word", "segment"]]] = Form(None),

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

        n: Optional[int] = Query(1),
):
    api_key = auth and auth.credentials or None

    async with ppu_flow(api_key, post='api-stt', n=n):
        file = await to_bytes(file)

        request = STTRequest(
            file=file,
            model=model,
            language=language,
            prompt=prompt,
            response_format=response_format,
            temperature=temperature,
            timestamp_granularities=timestamp_granularities
        )
        if model.startswith("whisper"):
            try:
                return await deepinfra_audio.asr(request)
            except Exception as e:
                logger.error(e)

        return await siliconflow_audio.asr(request)  # 兜底


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

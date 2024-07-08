#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : speech
# @Time         : 2023/12/26 14:12
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from meutils.ai_audio.tts import EdgeTTS
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.config_utils.lark_utils import get_next_token_for_polling
# from meutils.llm.openai_utils import ppu_flow

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from openai import AsyncOpenAI

from meutils.schemas.openai_types import TTSRequest

router = APIRouter()
TAGS = ["audio"]


@router.post("/audio/speech")
async def create_speech(
        request: TTSRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
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


@router.post("/audio/transcriptions")
async def create_transcriptions(
        file: UploadFile = File(...),
        model: str = Form("whisper-1"),
        language: Optional[str] = Form(None),
        prompt: Optional[str] = Form(None),
        response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] = Form("json"),
        temperature: Optional[float] = Form(None),

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        feishu_url: Optional[str] = Query("https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=NWOIr9"),
):
    groq_api_key = await get_next_token_for_polling(feishu_url=feishu_url)
    client = AsyncOpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")

    response_format = response_format if response_format in {"json", "text", "verbose_json"} else "verbose_json"

    response = await client.audio.transcriptions.create(
        file=(file.filename or file.file.name, file.file),
        model="whisper-large-v3",  # 必须是这个
        language=language,
        prompt=prompt,
        response_format=response_format,
        temperature=temperature,
        # extra_body={"url": "https://oss.chatfire.cn/data/demo.mp3"}
    )

    return response


@router.post("/audio/translations")
async def create_translations(
        file: UploadFile = File(...),
        model: str = Form("whisper-1"),
        prompt: Optional[str] = Form(None),
        response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] = Form("json"),
        temperature: Optional[float] = Form(None),

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        feishu_url: Optional[str] = Query("https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=NWOIr9"),
):
    groq_api_key = await get_next_token_for_polling(feishu_url=feishu_url)
    client = AsyncOpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")

    response_format = response_format if response_format in {"json", "text", "verbose_json"} else "verbose_json"

    response = await client.audio.translations.create(
        file=(file.filename or file.file.name, file.file),
        model="whisper-large-v3",  # 必须是这个
        prompt=prompt,
        response_format=response_format,
        temperature=temperature,
    )

    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

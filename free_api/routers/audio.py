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
from meutils.schemas.openai_types import TTSRequest
from meutils.config_utils.lark_utils import get_next_token_for_polling

from meutils.ai_audio.tts import EdgeTTS
from meutils.apis.voice_clone import fish

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status, Response
from fastapi.responses import JSONResponse, StreamingResponse

from openai import AsyncOpenAI

router = APIRouter()
TAGS = ["Audio"]


@router.post("/audio/speech")
async def create_speech(
        request: TTSRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        voice: Optional[str] = Query(None),  # todo: 枚举
):
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
    if len(request.voice) == 32:  # "bd2680a9372746faabc4ce8ac3f12eeb" 声音克隆 可以映射一波
        data = await fish.create_task(request)

        logger.debug(data)

        async with httpx.AsyncClient(timeout=30) as client:
            url = data.get("url")
            response = await client.get(url)
            return Response(content=response.content, media_type="application/octet-stream", headers={"url": url})

    else:
        data = request.model_dump()
        data["voice"] = voice or data["voice"]  # 支持很多种声音

        stream = await EdgeTTS().acreate_for_openai(**data)  # todo 优化

        # text/event-stream => application/octet-stream
        return StreamingResponse(stream, media_type=media_type)


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

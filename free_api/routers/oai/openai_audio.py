#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : elevenlabs
# @Time         : 2025/7/14 16:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.apis.fal import audio as fal_audio
from meutils.apis.ppio import audio as ppio_audio
from meutils.apis.audio import gitee as gitee_audio

from meutils.schemas.openai_types import TTSRequest, STTRequest

from meutils.llm.openai_utils import ppu_flow
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()
TAGS = ["Audio"]


@router.post("/speech")
async def text_to_speech(
        request: TTSRequest,

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),

        n: Optional[int] = 1,  # 是否计费, 放中转不计费

):
    model = request.model.lower()
    async with atry_catch(f"{model}", api_key=api_key, callback=send_message, request=request):

        # todo 增加按量计费
        if model in {
            "minimax-speech-02-turbo", "minimax-speech-02-hd",
            "fal-ai/minimax/speech-02-turbo", "fal-ai/minimax/speech-02-hd",
        }:
            if request.voice.lower().startswith("Voice") or model.startswith("fal"):  # fal 克隆
                request.model = f"""fal-ai/minimax/{model.removeprefix("minimax-").removeprefix("fal-ai/minimax/")}"""
                response = await fal_audio.text_to_speech(request, api_key)
            else:
                response = await ppio_audio.text_to_speech(request, api_key)

            if isinstance(response, dict): return response
            return StreamingResponse([response], media_type="audio/mpeg")

        async with ppu_flow(api_key, post=model, dynamic=True, n=n):
            response = await gitee_audio.text_to_speech(request)
            if isinstance(response, dict): return response

            return StreamingResponse([response.content], media_type="audio/mpeg")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/openai/v1/audio')

    app.run()

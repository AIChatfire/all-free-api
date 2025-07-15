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

from meutils.apis.audio import gitee
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

):
    model = request.model
    # model = "api-oss"
    async with atry_catch(f"{model}", api_key=api_key, callback=send_message, request=request):
        response = await gitee.text_to_speech(request)

        async with ppu_flow(api_key, post=model, dynamic=True):
            if isinstance(response, dict): return response
            return StreamingResponse([response.content], media_type="audio/mpeg")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/openai/v1/audio')

    app.run()

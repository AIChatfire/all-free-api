#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fish
# @Time         : 2024/10/24 11:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.apis.audio.fish import TTSRequest, create_tts, create_tts_model

from meutils.llm.openai_utils import ppu_flow
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse

router = APIRouter()
TAGS = ["Audio"]


@router.post("/v1/tts")
async def _create_tts(
        request: TTSRequest,

        response_format: Optional[str] = Query(None),

        api_key: Optional[str] = Depends(get_bearer_token),

):
    async with ppu_flow(api_key, post="official-api-fish-tts"):
        data = await create_tts(request, response_format=response_format)

        if response_format == 'url':
            return data
        return Response(content=data, media_type="application/octet-stream")


@router.post("/model")
async def _create_model(
        title: str = Form('chatfire-tts-model'),
        voices: List[UploadFile] = File(...),
        texts: Optional[List[str]] = Form(None),

        auth: Optional[str] = Depends(get_bearer_token),

):
    api_key = auth

    async with ppu_flow(api_key, post="official-api-fish-model"):
        voices = [await voice.read() for voice in voices]
        return await create_tts_model(title, voices, texts)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()
    app.include_router(router)
    app.run(port=9000)

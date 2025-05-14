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
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.jimeng.audio import create
from meutils.schemas.openai_types import TTSRequest, STTRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status, Response
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()
TAGS = ["Audio"]


@router.post("/audio/speech")
async def create_speech(
        request: TTSRequest,

        api_key: Optional[str] = Depends(get_bearer_token),

        n: Optional[int] = Query(1),  # 默认收费
):
    logger.debug(request.model_dump_json(indent=4))

    n = n and np.ceil(len(request.input) / 1000)
    async with ppu_flow(api_key, post='api-tts', n=n):
        stream = await create(request)

        if request.response_format == "url":
            return {"url": stream}

        return StreamingResponse(stream, media_type="application/octet-stream")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

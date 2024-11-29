#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ocr
# @Time         : 2024/9/27 16:50
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.apis.hf import got_ocr

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow


from meutils.apis.hf import got_ocr
from meutils.schemas.ocr_types import OCRRequest

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["VISION"]

ChatCompletionResponse = Union[ChatCompletion, List[ChatCompletionChunk]]


@router.post("/ocr")
async def create_ocr(
        request: OCRRequest,
        auth: Optional[str] = Depends(get_bearer_token),
):
    api_key = auth
    logger.debug(request.model_dump_json(indent=4))

    task_type = "api-ocr" if request.mode == "simple" else "api-ocr-pro"

    async with ppu_flow(api_key, post=task_type):
        if request.mode == "simple":
            pass
        else:
            text, rendered_html = await got_ocr.create(request)
            return {
                "text": text,
                "html": rendered_html
            }


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

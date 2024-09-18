#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : html2image
# @Time         : 2024/9/18 16:57
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import create_chat_completion_chunk, appu, ppu_flow
from meutils.serving.fastapi.routers.screenshot import capture_screenshot, ScreenshotRequest
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Path

router = APIRouter()
TAGS = ["预处理"]


@router.post("/html2image")
async def create_chat_completions(
        request: ScreenshotRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    async with ppu_flow(api_key, post="api-html2image"):
        return await capture_screenshot(request)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()
    app.include_router(router)
    app.run(port=8000)

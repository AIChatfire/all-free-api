#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/10/13 13:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.oss.minio_oss import Minio
from meutils.io.files_utils import to_url, to_bytes

from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import appu, ppu_flow
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.apis.voice_clone import fish
from meutils.apis.textin import document_process as textin_fileparser
from meutils.apis.kuaishou import kolors, klingai

from meutils.schemas.video_types import Video, SoraVideoRequest
from meutils.apis.runware import videos as runware_videos

from enum import Enum
from openai import OpenAI
from openai._types import FileTypes
from openai.types.file_object import FileObject

from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse, RedirectResponse

router = APIRouter()
TAGS = ['Videos']


@router.post("/videos")  # 核心
async def create_video(

        model: str = Form(...),
        prompt: str = Form(...),

        input_reference: Optional[List[UploadFile]] = File(None),

        seconds: Optional[str] = Form(None),
        size: Optional[str] = Form(None),

        api_key: Optional[str] = Depends(get_bearer_token),

):
    request = SoraVideoRequest(
        model=model,
        prompt=prompt,
        seconds=seconds,
        size=size or "720x1280",
    )

    if input_reference:
        files = [await file.read() for file in input_reference]
        request.input_reference = files

    _ = await runware_videos.create_task(
        request,
        api_key,
    )

    return _


@router.get("/videos/{id}")
async def get_video(
        id: str,
        # auth: Optional[str] = Depends(get_bearer_token),
):
    video = await runware_videos.get_task(id)
    return video


@router.get("/videos/{id}/content")
async def get_file_content(
        id: str,
):
    video = await get_video(id)
    # file_content = await to_bytes(video.video_url)
    # return Response(content=file_content, media_type="application/octet-stream")
    return RedirectResponse(
        video.video_url,  # 带签名的临时 URL 更佳
        status_code=302
    )


#

# @router.get("/files")
# async def get_files(
#         api_key: Optional[str] = Depends(get_bearer_token),
# ):
#     return client.files.list()
#
#
# @router.delete("/files/{file_id}")
# async def delete_file(
#         file_id: str,
#         api_key: Optional[str] = Depends(get_bearer_token),
# ):
#     return client.files.delete(file_id=file_id)
#

if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, "/v1")
    app.run(port=8000)

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
from meutils.io.files_utils import to_url

from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import appu, ppu_flow
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.apis.voice_clone import fish
from meutils.apis.textin import document_process as textin_fileparser
from meutils.apis.kuaishou import kolors, klingai

from meutils.schemas.video_types import Video

from enum import Enum
from openai import OpenAI
from openai._types import FileTypes
from openai.types.file_object import FileObject

from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse

router = APIRouter()
TAGS = ['Videos']


@router.post("/videos")  # 核心
async def create_video(

        model: str = Form(...),
        prompt: str = Form(...),

        input_reference: Optional[UploadFile] = File(None),

        seconds: Optional[str] = Form(None),
        size: Optional[str] = Form(None),

        api_key: Optional[str] = Depends(get_bearer_token),

):
    pass

    return Video(
        model=model,

        seconds=seconds,
        size=size,
    )


@router.get("/files/{file_id}")
async def get_file(
        file_id: str,
        # auth: Optional[str] = Depends(get_bearer_token),
):
    return client.files.retrieve(file_id=file_id)


@router.get("/files/{file_id}/content")
async def get_file_content(
        file_id: str,
        api_key: Optional[str] = Depends(get_bearer_token),

):
    if Purpose.textin_fileparser in file_id:
        file_content = await redis_aclient.get(file_id)
    else:
        file_content = client.files.content(file_id=file_id).text

    return Response(content=file_content, media_type="application/octet-stream")


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
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

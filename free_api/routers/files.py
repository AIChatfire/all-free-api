#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : files
# @Time         : 2023/12/29 14:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : TODO

import jsonpath

from meutils.pipe import *
from meutils.oss.minio_oss import Minio
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import appu, ppu_flow
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.apis.textin import textin_fileparser
from meutils.apis import fish
from meutils.apis.kuaishou import kolors, klingai

from enum import Enum
from openai import OpenAI
from openai._types import FileTypes
from openai.types.file_object import FileObject
from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse

router = APIRouter()
TAGS = ['文档智能']

client = OpenAI(
    api_key=os.getenv('MOONSHOT_API_KEY'),
    base_url=os.getenv('MOONSHOT_BASE_URL'),
)


class Purpose(str, Enum):
    # 存储
    oss = "oss"
    upload = "upload"

    # 文档智能
    chatfire_fileparser = "textin-fileparser"
    file_extract = "textin-fileparser"
    moonshot_fileparser = "moonshot-fileparser"
    textin_fileparser = "textin-fileparser"

    # 语音克隆 tts  Voice clone
    tts = "tts"

    assistants = "assistants"
    fine_tune = "fine-tune"

    # 图 音频 视频
    kling = "kling"
    kolors = "kolors"


@router.get("/files")
async def get_files(
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    return client.files.list()


@router.get("/files/{file_id}")
async def get_file(
        file_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None

    return client.files.retrieve(file_id=file_id)


@router.get("/files/{file_id}/content")
async def get_file_content(
        file_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None

    if Purpose.textin_fileparser in file_id:
        file_content = await redis_aclient.get(file_id)
    else:
        file_content = client.files.content(file_id=file_id).text

    await appu("ppu-1", api_key)  # 计费
    return Response(content=file_content, media_type="application/octet-stream")


@router.delete("/files/{file_id}")
async def delete_file(
        file_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    return client.files.delete(file_id=file_id)


@router.post("/files")  # 核心
async def upload_files(
        file: UploadFile = File(...),
        purpose: Purpose = Form(...),
        url: Optional[str] = Form(None),
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth and auth.credentials or None

    file_object = FileObject.construct(

        filename=file.filename,
        bytes=file.size,

        id=shortuuid.random(),
        created_at=int(time.time()),
        object='file',

        purpose=purpose,
        status="uploaded",

        url=url
    )
    logger.debug(file_object)

    if purpose in {purpose.oss, purpose.upload}:
        async with ppu_flow(api_key, post="ppu-01"):
            bucket_name = "files"
            extension = Path(file.filename).suffix
            filename = f"{shortuuid.random()}{extension}"
            backgroundtasks.add_task(
                Minio().put_object_for_openai,
                bucket_name=bucket_name,
                file=file,
                filename=filename)

            file_url = Minio().get_file_url(filename)
            file_object.url = file_url

            return file_object

    elif purpose in {purpose.textin_fileparser, purpose.chatfire_fileparser, purpose.file_extract}:
        async with ppu_flow(api_key, post="ppu-01"):

            response_data = await textin_fileparser(file.file.read())
            markdown_text = jsonpath.jsonpath(response_data, "$..markdown")  # False or []
            markdown_text = markdown_text and markdown_text[0]

            file_object.status = "processed" if markdown_text else "error"
            file_object.status_details = response_data

            if markdown_text:
                await redis_aclient.set(file_object.id, markdown_text, ex=3600 * 24 * 7)
            return file_object

    elif purpose == purpose.moonshot_fileparser:
        async with ppu_flow(api_key, post="ppu-01"):

            file_object = client.files.create(file=(file.filename, file.file), purpose="file-extract")

            return file_object

    elif purpose == purpose.kolors:
        async with ppu_flow(api_key, post="ppu-01"):
            url = await kolors.upload(file.file.read())
            file_object.url = url
            return file_object

    elif purpose == purpose.kling:  # 1毛
        async with ppu_flow(api_key, post="ppu-1"):
            url = await klingai.upload(file.file.read())
            file_object.url = url
            return file_object

    elif purpose == purpose.tts:  # todo: 语音克隆
        file_object = await fish.create_file_for_openai(file)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

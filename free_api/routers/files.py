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
from meutils.io.files_utils import to_url
from meutils.io.openai_files import file_extract

from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import appu, ppu_flow
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.apis.voice_clone import fish
from meutils.apis.textin import document_process as textin_fileparser
from meutils.apis.kuaishou import kolors, klingai

from meutils.schemas.task_types import Purpose

from enum import Enum
from openai import OpenAI
from openai._types import FileTypes
from openai.types.file_object import FileObject
from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse

router = APIRouter()
TAGS = ['Files']

client = OpenAI(
    api_key=os.getenv('MOONSHOT_API_KEY'),
    base_url=os.getenv('MOONSHOT_BASE_URL'),
)


@router.post("/files")  # 核心
async def upload_files(
        file: UploadFile = File(...),
        purpose: Purpose = Form(...),
        auth: Optional[str] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,

        vip: Optional[bool] = Query(False),

        response_format: Optional[str] = Query(None),

):
    api_key = auth

    vip = 'vip' in purpose or vip

    file_object = FileObject.construct(

        filename=file.filename,
        bytes=file.size,

        id=shortuuid.random(),
        created_at=int(time.time()),
        object='file',

        purpose=purpose,
        status="uploaded",

        data=None,
        url=None,
    )
    logger.debug(file_object)
    logger.debug(file.headers)
    logger.debug(file.content_type)
    logger.debug(purpose)
    logger.debug(purpose.value)

    if purpose in {purpose.oss}:  # or purpose not in Purpose.__members__

        async with ppu_flow(api_key, post="api-oss"):
            # if url:  # todo: 转存 url文件或者file view

            bucket_name = "files"
            extension = Path(file.filename).suffix
            filename = f"{shortuuid.random()}{extension}"

            # backgroundtasks.add_task(
            #     Minio().put_object_for_openai,
            #     bucket_name=bucket_name,
            #     file=file,  # 异步错误 ValueError: I/O operation on closed file.
            #     filename=filename
            # )

            file_object = await Minio().put_object_for_openai(
                bucket_name=bucket_name,
                file=file,  # 异步错误 ValueError: I/O operation on closed file.
                filename=filename
            )

            file_url = Minio().get_file_url(filename)
            file_object.url = file_url

            return file_object

    elif purpose in {purpose.textin_fileparser, purpose.file_extract}:
        async with ppu_flow(api_key, post="api-pdf-to-markdown"):

            response_data = await textin_fileparser(await file.read())
            markdown_text = jsonpath.jsonpath(response_data, "$..markdown")  # False or []
            markdown_text = markdown_text and markdown_text[0]

            file_object.status = "processed" if markdown_text else "error"
            file_object.data = response_data

            if markdown_text:
                await redis_aclient.set(file_object.id, markdown_text, ex=1 * 3600 * 24)
            return file_object

    elif purpose == purpose.moonshot_fileparser:  ###########
        async with ppu_flow(api_key, post="api-file-to-text"):

            file_object = client.files.create(file=(file.filename, file.file), purpose="file-extract")

            file_content = client.files.content(file_id=file_object.id).text
            file_object.data = file_content

            # await redis_aclient.set(file_object.id, file_object.data, ex=1 * 3600 * 24)
            # 定期清理

            return file_object



    elif purpose.startswith(purpose.kling):
        file_task = await klingai.upload(await file.read(), vip=vip)

        file_object.id = file_task.id
        file_object.url = file_task.url
        file_object.data = file_task.data
        file_object.status = "uploaded" if file_task.url else "error"

        return file_object


    elif purpose == purpose.voice_clone:
        async with ppu_flow(api_key, post="api-voice-clone"):
            file_object = await fish.create_file_for_openai(file)
            return file_object


@router.get("/files/{file_id}")
async def get_file(
        file_id: str,
        # auth: Optional[str] = Depends(get_bearer_token),
):
    return client.files.retrieve(file_id=file_id)


@router.get("/files")
async def get_files(
        api_key: Optional[str] = Depends(get_bearer_token),
):
    return client.files.list()


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


@router.delete("/files/{file_id}")
async def delete_file(
        file_id: str,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    return client.files.delete(file_id=file_id)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

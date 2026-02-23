#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : files
# @Time         : 2023/12/29 14:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : TODO


from meutils.pipe import *
from meutils.oss.minio_oss import Minio
from meutils.io.files_utils import to_url
from meutils.io.openai_files import file_extract
from meutils.llm.clients import moonshot_client

from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import appu, ppu_flow, billing_utils
from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from meutils.schemas.openai_types import FileObject

from openai import OpenAI
from openai._types import FileTypes
# from openai.types.file_object import FileObject
from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse

router = APIRouter()
TAGS = ['Files']


@router.post("/files")  # 核心
async def upload_files(
        file: UploadFile = File(...),
        purpose: Optional[str] = Form(None),
        # api_key: Optional[str] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,

        response_format: Optional[str] = Query(None),

):
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

    file_object = FileObject(
        filename=file.filename,
        bytes=file.size,
        purpose=purpose,
    )

    if purpose == "file-extract":  ###########

        file_data = await file_extract(await file.read(), filename=file.filename)
        file_object.metadata = file_data

        logfire.info("{file=!r}", file=file_object, _tags=[purpose])   # 保留转义

        return file_object

    elif purpose in {"oss", "url"}:  # 中国 国外
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

        url = await Minio().upload(
            file=await file.read(),
            filename=file.filename,
            content_type=content_type
        )

        file_object = FileObject(
            filename=file.filename,
            bytes=file.size,
            purpose=purpose,
            url=url
        )
        logfire.info("{file=!r}", file=file_object, _tags=[purpose])  # 保留转义

        return file_object


@router.get("/files/{file_id}")
async def get_file(
        file_id: str,
):
    return moonshot_client.files.retrieve(file_id=file_id)


@router.get("/files")
async def get_files():
    return moonshot_client.files.list()


@router.get("/files/{file_id}/content")
async def get_file_content(
        file_id: str,
):
    file_content = moonshot_client.files.content(file_id=file_id).text

    return Response(content=file_content, media_type="application/octet-stream")


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, ):
    return moonshot_client.files.delete(file_id=file_id)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

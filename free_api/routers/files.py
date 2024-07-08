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
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import appu
from meutils.apis.textin import textin_fileparser
from meutils.apis import fish

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from enum import Enum
from openai import OpenAI
from openai._types import FileTypes
from openai.types.file_object import FileObject
from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse

router = APIRouter()

client = OpenAI(
    api_key=os.getenv('MOONSHOT_API_KEY'),
    base_url=os.getenv('MOONSHOT_BASE_URL'),
)


class Purpose(str, Enum):
    # 文档智能
    chatfire_fileparser = "textin-fileparser"
    moonshot_fileparser = "moonshot-fileparser"
    textin_fileparser = "textin-fileparser"
    # 语音克隆 tts  Voice clone
    tts = "tts"

    file_extract = "file-extract"
    assistants = "assistants"
    fine_tune = "fine-tune"


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
        # return_url=Form(...)
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None

    if purpose in {purpose.textin_fileparser, purpose.chatfire_fileparser}:

        response_data = await textin_fileparser(file.file.read())
        markdown_text = jsonpath.jsonpath(response_data, "$..markdown")  # False or []
        markdown_text = markdown_text and markdown_text[0]

        file_object = FileObject.construct(

            filename=file.filename,  # result.get("file_name")
            bytes=file.size,

            id=shortuuid.random(),
            created_at=int(time.time()),
            object='file',

            purpose=purpose,
            status="processed" if markdown_text else "error",
            status_details=response_data
        )

        # logger.debug(f"file-{file_object.purpose}:{file_object.id}")
        if markdown_text:
            file_object.id = f"file:{file_object.purpose}-{file_object.id}"
            await redis_aclient.set(file_object.id, markdown_text, ex=3600 * 24 * 7)

    elif purpose == purpose.tts:
        file_object = await fish.create_file_for_openai(file)

    else:  # 其他走 kimi

        file_object = client.files.create(file=(file.filename, file.file), purpose="file-extract")

    await appu("ppu-001", api_key)  # 计费
    return file_object


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

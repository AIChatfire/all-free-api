#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : files
# @Time         : 2023/12/29 14:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import appu

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
    file_extract = "file-extract"
    assistants = "assistants"
    fine_tune = "fine-tune"


@router.get("/files")
async def get_files(
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")

    try:
        _ = per_create(api_key=api_key)  # 按次计费
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return client.files.list()


@router.get("/files/{file_id}")
async def get_file(
        file_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")
    try:
        _ = per_create(api_key=api_key)  # 按次计费
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return client.files.retrieve(file_id=file_id)


@router.get("/files/{file_id}/content")
async def get_file_content(
        file_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")
    try:
        _ = per_create(api_key=api_key)  # 按次计费
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    file_content = client.files.content(file_id=file_id).text
    return Response(content=file_content, media_type="application/octet-stream")


@router.delete("/files/{file_id}")
async def delete_file(
        file_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")

    try:
        _ = per_create(api_key=api_key)  # 按次计费
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return client.files.delete(file_id=file_id)


@router.post("/files")  # 同名文件会被覆盖
async def upload_files(
        file: UploadFile = File(...),
        purpose: Purpose = Form(...),
        # return_url=Form(...)
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")

    try:
        _ = per_create(api_key=api_key, model='per-file')  # 按次计费
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # kimi官方api
    if 'kimi-api':
        file_object = client.files.create(file=(file.filename, file.file), purpose="file-extract")

    return file_object


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

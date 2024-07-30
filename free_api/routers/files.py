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

from meutils.apis.voice_clone import fish
from meutils.apis.textin import textin_fileparser
from meutils.apis.kuaishou import kolors, klingai
from meutils.apis.sunoai import suno
from meutils.apis.chatglm import glm_video

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


class Purpose(str, Enum):
    # 存储
    oss = "oss"

    # 文档智能
    file_extract = "file-extract"
    moonshot_fileparser = "moonshot-fileparser"
    textin_fileparser = "textin-fileparser"

    # 图 音频 视频
    kling = "kling"
    kolors = "kolors"
    suno = "suno"
    cogvideox = "cogvideox"

    # 语音克隆 tts  Voice clone
    tts = "tts"
    voice_clone = "voice-clone"

    # todo
    assistants = "assistants"
    fine_tune = "fine-tune"


@router.post("/files")  # 核心
async def upload_files(
        file: UploadFile = File(...),
        purpose: Purpose = Form(...),
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

        url=None
    )
    logger.debug(file_object)
    logger.debug(file.headers)
    logger.debug(file.content_type)

    if purpose in {purpose.oss}:
        async with ppu_flow(api_key, post="ppu-01"):
            # if url:  # todo: 转存 url文件或者file view

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

    elif purpose in {purpose.textin_fileparser, purpose.file_extract}:
        async with ppu_flow(api_key, post="ppu-01"):

            response_data = await textin_fileparser(await file.read())
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
            url = await kolors.upload(await file.read())
            # todo: 内容审核

            file_object.url = url
            return file_object

    elif purpose == purpose.kling:  # 1毛
        async with ppu_flow(api_key, post="ppu-1"):
            url = await klingai.upload(await file.read())
            if not isinstance(url, str):
                raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail=url)

            file_object.url = url
            return file_object

    elif purpose == purpose.suno:  # 1毛
        async with ppu_flow(api_key, post="api-sunoai-audio"):
            clip_data, token = await suno.upload(await file.read(), title=file.filename or file.file.name)  # clip
            if not clip_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=clip_data)

            # 获取clip_id
            file_object.id, file_object.duration = jsonpath.jsonpath(clip_data, "$..[id,duration]")
            file_object.data = clip_data

            await redis_aclient.set(file_object.id, token, ex=1 * 24 * 3600)
            return file_object

    elif purpose == purpose.cogvideox:
        async with ppu_flow(api_key, post="ppu-01"):
            data, token = await glm_video.upload(await file.read())  # clip

            file_object.data = data
            file_object.id = data['result']['source_id']
            file_object.url = data['result']['source_url']

            await redis_aclient.set(file_object.id, token, ex=1 * 24 * 3600)
            return file_object

    elif purpose == purpose.voice_clone:
        async with ppu_flow(api_key, post="api-voice-clone"):
            file_object = await fish.create_file_for_openai(file)
            return file_object


@router.get("/files/{file_id}")
async def get_file(
        file_id: str,
        # auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    return client.files.retrieve(file_id=file_id)


@router.get("/files")
async def get_files(
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    return client.files.list()


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


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, VERSION_PREFIX)
    app.run(port=9000)

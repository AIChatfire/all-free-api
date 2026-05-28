#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/10/13 13:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo 其他 sora 格式标准化
import json

from meutils.pipe import *
from meutils.oss.minio_oss import Minio
from meutils.io.files_utils import to_url, to_bytes, to_url_fal, to_base64, guess_mime_type, do_file_data

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from meutils.schemas.video_types import Video, SoraVideoRequest
from meutils.apis.async_tasks.tasks import AsyncTasks

from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse, RedirectResponse
from starlette.datastructures import UploadFile as _UploadFile

router = APIRouter()
TAGS = ['async-task']


@router.post("/videos")  # 核心
async def create_task(  # 通用型
        request: SoraVideoRequest,

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: Optional[dict] = Depends(get_headers),

):
    logger.debug(headers)
    if len(str(request)) < 2000: logger.debug(bjson(request))

    base_url = headers.get("base-url") or headers.get("x-base-url") or ""

    if '|' in api_key:
        base_url, api_key = api_key.split('|', maxsplit=1)  # 区分渠道

    try:
        task = AsyncTasks(base_url=base_url, api_key=api_key)
        return await task.create(request)
    except Exception as e:  # todo
        # if backup_api_key:
        #     if any(i.lower() in str(e).lower() for i in {
        #         'QuotaExceeded', 'rate limit', 'quota', 'insufficient funds', 'over quota', 'over limit', 'exceeded',
        #         'too many requests', 'request limit', 'rate limit', 'limit exceeded', 'overloaded', 'busy',
        #         'unavailable'
        #     }):
        #         logger.error(f"create video error: {e}, retrying with backup api key")
        #
        #         videos = OpenAIVideos(base_url=base_url, api_key=backup_api_key)
        #         return await videos.create(request)

        raise e


@router.get("/videos/{id:path}")
async def get_task(
        id: str,
        api_key: Optional[str] = Depends(get_bearer_token),

        headers: Optional[dict] = Depends(get_headers),
):
    base_url = headers.get("base-url") or headers.get("x-base-url") or ""

    logger.debug(f"get base_url: {base_url}")  # 这里好像未生效 todo 确认
    logger.debug(f"get api_key: {api_key}")  # 这里好像未生效 todo 确认

    return await AsyncTasks().get(id)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    VERSION_PREFIX = '/v1'

    app = App()
    app.include_router(router, "/v1")
    app.run(port=8000)
    478354211820584968

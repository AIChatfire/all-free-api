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

from meutils.db.redis_db import redis_aclient
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from meutils.serving.fastapi.utils import form_to_dict

from meutils.schemas.video_types import Video, SoraVideoRequest
from meutils.apis.runware import videos as runware_videos
from meutils.apis.videos.videos import OpenAIVideos

from fastapi import APIRouter, File, UploadFile, Query, Form, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response, FileResponse, RedirectResponse
from starlette.datastructures import UploadFile as _UploadFile

router = APIRouter()
TAGS = ['Videos']


@router.get("/dev/v1/videos/{id:path}")
async def get_video(
        id: str
):
    return {
        "id": id,
        "object": "video",
        "model": "sora-2",
        "created_at": 1640995200,
        "status": "completed",
        "progress": 0,
        "error": {"code": "4", "message": "error"},  # code 必须字符串
        "prompt": "火起来",

        "metadata": {"task_id": id}
    }


@router.post("/dev/v1/videos")  # 核心
async def create_video(  # todo 通用型

        request: Request,
        model: str = Form(...),
        prompt: str = Form(...),

        input_reference: Optional[Union[List[str], List[UploadFile]]] = File(None),

        seconds: Optional[str] = Form(None),
        size: Optional[str] = Form(None),

        image: Optional[List[str]] = Form(None),

        n: Optional[int] = Form(None),
        error: Optional[str] = Form(None),
        status: Optional[str] = Form(None),
        progress: Optional[int] = Form(None),

        headers: Optional[dict] = Depends(get_headers),
):
    logger.debug(image)
    logger.debug(input_reference)
    if n == 0:
        return Video(
            status=status or 'failed',
            id='9888bd5a-b87c-40e3-8bbf-c8914464ecf0',
            completed_at=None, created_at=1769647073,
            error={'code': '2400002', 'httpCode': 0, 'message': '文案违反社区规范，请更换文案后重试',
                   'serviceTime': 1769647073, 'requestID': '545f3033-0e38-49cb-912d-b58a6e499fea',
                   'debugInfo': '2400002', 'serverAlert': 0},
            progress=progress or 0, # 100?
            prompt=None, remixed_from_video_id=None, seconds=None, size=None, video_url=None,
        )


    elif n == 1:
        return {
            "id": "video_123",
            "object": "video",
            "model": "sora-2",
            "created_at": 1640995200,
            "status": "processing",
            "progress": 0,
            "error": json.loads(error)
        }

    if n == 2:
        return {
            "id": "video_123",
            "object": "video",
            "model": "sora-2",
            "created_at": 1640995200,
            "status": "processing",
            "progress": 0
        }

    elif n == 3:
        return {
            "id": "video_123",
            "object": "video",
            "model": "sora-2",
            "created_at": 1640995200,
            "status": "processing",
            "progress": 0,
            "error": {"message": "error"}  # 少正常
        }

    elif n == 4:
        return {
            "id": "video_123",
            "object": "video",
            "model": "sora-2",
            "created_at": 1640995200,
            "status": "processing",
            "progress": 0,
            "error": {"code": 4, "message": "error"}  # code 必须字符串
        }

    elif n == 5:
        return {
            "id": "video_123",
            "object": "video",
            "model": "sora-2",
            "created_at": 1640995200,
            "status": "processing",
            "progress": 0,
            "error": {"code": "1", "message": "error"}
        }

    elif n == 6:
        return {
            "id": "video_123",
            "object": "video",
            "model": "sora-2",
            "created_at": 1640995200,
            "status": "processing",
            "progress": 0,
            "error": {"code": "1", "message": "error", 'xx': 'xx'}
        }

    formdata = await request.form()
    _ = form_to_dict(formdata, file2json=True)

    logger.debug(_)
    return Video(
        **_
    )


@router.post("/videos")  # 核心
async def create_video(  # todo 通用型
        request: Request,

        model: str = Form(...),
        prompt: str = Form(...),

        input_reference: Optional[Union[List[UploadFile], List[str]]] = Form(None),  # [""]

        seconds: Optional[str] = Form(None),
        size: Optional[str] = Form(None),

        # url or base64
        first_frame_image: Optional[Union[UploadFile, str]] = Form(None),  # Part exceeded maximum size of 1024KB
        last_frame_image: Optional[Union[UploadFile, str]] = Form(None),

        image: Optional[Union[UploadFile, str]] = Form(None),
        audio: Optional[Union[UploadFile, str]] = Form(None),
        video: Optional[Union[UploadFile, str]] = Form(None),

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: Optional[dict] = Depends(get_headers),

        # 额外参数
        enhance_prompt: Optional[bool] = Form(None),
        generate_audio: Optional[bool] = Form(None),

        template: Optional[str] = Form(None),  # 视频特效模板
        style: Optional[str] = Form(None),
        callback_url: Optional[str] = Form(None),

):
    # logger.debug(image)  # ['image1', 'image2'] ['image1']
    logger.debug(input_reference)  # None [""] [UploadFile()]

    request_mode = headers.get("x-request-mode") or ""
    base_url = headers.get("base-url") or headers.get("x-base-url") or ""
    input_reference_format = headers.get("input-reference-format") or ""

    logger.debug(headers)

    content_type = None
    if model.startswith(("doubao-seedance")) or any(i in base_url for i in {'aimlapi', 'hailuo'}):
        content_type = "image/jpeg"

    if request_mode:  # 通用模式
        formdata = await request.form()
        formdata = form_to_dict(formdata)

        logger.debug(formdata)
        formdata.pop("input_reference", None)  # 单独处理
        request = SoraVideoRequest(**formdata)
        logany(request)
    else:

        input_reference, first_frame_image, last_frame_image = await do_file_data(
            [input_reference, first_frame_image, last_frame_image],
            input_reference_format=input_reference_format,
            content_type=content_type
        )

        request = SoraVideoRequest(
            model=model,
            prompt=prompt,
            seconds=seconds,
            size=size,

            # file
            input_reference=input_reference,
            first_frame_image=first_frame_image,
            last_frame_image=last_frame_image,
            image=image,
            audio=audio,
            video=video,

            # 额外参数
            enhance_prompt=enhance_prompt,
            generate_audio=generate_audio,
            template=template,
            style=style,

            callback_url=callback_url
        )

    if len(str(request)) < 2000: logger.debug(request)

    ###### todo 放弃
    if "runware" in base_url:
        _ = await runware_videos.create_task(
            request,
            api_key,
        )
        return _
    ##########################################

    videos = OpenAIVideos(base_url=base_url, api_key=api_key)
    return await videos.create(request)


@router.get("/videos/{id:path}")
async def get_video(
        id: str,
        # auth: Optional[str] = Depends(get_bearer_token),

        headers: Optional[dict] = Depends(get_headers),
):
    base_url = headers.get("base-url") or headers.get("x-base-url") or ""

    logger.debug(f"get base_url: {base_url}")  # 这里好像未生效

    return await OpenAIVideos().get(id)


@router.get("/videos/{id:path}/content")
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/10/17 17:04
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.decorators.contextmanagers import try_catch, atry_catch
from meutils.notice.feishu import send_message_for_images

from meutils.io.files_utils import to_bytes
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.textin import document_process as textin_process
from meutils.apis.baidu.bdaitpzs import image_process as baidu_process
from meutils.apis.hunyuan.image_tools import image_process as hunyuan_process
from meutils.apis.images.edits import edit_image
from meutils.apis.hf import kolors_virtual_try_on
from meutils.apis.images.recraft import edit_image as recraft_edit_image

from meutils.schemas.image_types import ImageProcess, ImageRequest
from meutils.schemas.image_types import HUNYUAN_TASKS, HunyuanImageProcessRequest
from meutils.schemas.image_types import TEXTIN_TASKS, TextinImageProcessRequest
from meutils.schemas.image_types import BAIDU_TASKS, BaiduImageProcessRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, HTTPException, Request, status

router = APIRouter()
TAGS = ["AITOOLS_IMAGES"]


@router.post("/images/edits")
async def generate(
        request: ImageProcess,
        api_key: Optional[str] = Depends(get_bearer_token),

        n: Optional[int] = Query(1),  # 默认收费
):
    logger.debug(request)
    async with ppu_flow(api_key, post=f"api-images-edits-{request.model}", n=n):
        response = await edit_image(request)
        return response


@router.post("/images/virtual-try-on")
async def generate(
        request: kolors_virtual_try_on.KolorsTryOnRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(request.model_dump_json(indent=4))
    # return await text_to_image.create(request)

    logger.debug(request)
    async with ppu_flow(api_key, post="api-kolors-virtual-try-on"):
        data = await kolors_virtual_try_on.create(request)
        return data


@router.post("/images")
async def image_process(
        request: dict = Body(...),
        response_format: str = Query("url"),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    logger.debug(bjson(request))

    task = request.get("task")
    if task in HUNYUAN_TASKS:  # hunyuan
        request = HunyuanImageProcessRequest(**request)
        async with ppu_flow(api_key, post=f"api-aitools"):
            data = await hunyuan_process(request)
            return data

    elif task in TEXTIN_TASKS:
        request = TextinImageProcessRequest(**request)
        async with ppu_flow(api_key, post=f"api-aitools"):
            file = await to_bytes(request.image)
            data = await textin_process(file, service=request.task, response_format=response_format)
            return data

    elif task in BAIDU_TASKS:
        request = BaiduImageProcessRequest(**request)
        async with ppu_flow(api_key, post=f"api-aitools"):
            data = await baidu_process(request)
            return data

    else:
        raise Exception(f"请填写正确的 Task：{task}")


@router.post("/recraft/v1/images/generativeUpscale")  # form data
async def _recraft_edit_image(
        file: UploadFile = File(...),
        response_format: str = Form("url"),

):
    image = await file.read()
    async with atry_catch("/recraft/v1/images/generativeUpscale", callback=send_message_for_images):
        try:
            response = await recraft_edit_image(image)
            return response
        except Exception as e:
            try:
                request = ImageProcess(
                    model="clarity",
                    image=image,
                )
                response = await edit_image(request)
                return {"image": {"url": response.data[0].url}}

            except Exception as e:
                raise


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

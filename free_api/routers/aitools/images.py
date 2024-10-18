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
from meutils.io.files_utils import to_bytes
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.textin import document_process as textin_process
from meutils.apis.baidu.bdaitpzs import image_process as baidu_process
from meutils.apis.hunyuan.image_tools import image_process as hunyuan_process

from meutils.schemas.image_types import HUNYUAN_TASKS, HunyuanImageProcessRequest
from meutils.schemas.image_types import TEXTIN_TASKS, TextinImageProcessRequest
from meutils.schemas.image_types import BAIDU_TASKS, BaiduImageProcessRequest

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header, Body

router = APIRouter()
TAGS = ["图片处理工具"]


@router.post("/v1/images")
async def image_process(
        request: dict = Body(...),
        response_format: str = Query("url"),
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    logger.debug(request)

    api_key = auth and auth.credentials or None

    task = request.get("task")
    if task in HUNYUAN_TASKS:  # hunyuan
        request = HunyuanImageProcessRequest(**request)
        async with ppu_flow(api_key, post=f"api-aitools-{request.task}"):
            data = await hunyuan_process(request)
            return data

    elif task in TEXTIN_TASKS:
        request = TextinImageProcessRequest(**request)
        async with ppu_flow(api_key, post=f"api-aitools-{request.task}"):
            file = await to_bytes(request.image)
            data = await textin_process(file, service=request.task, response_format=response_format)
            return data

    elif task in BAIDU_TASKS:
        request = BaiduImageProcessRequest(**request)
        async with ppu_flow(api_key, post=f"api-aitools-{request.task}"):
            data = await baidu_process(request)
            return data

    else:
        raise Exception(f"请填写正确的 Task：{task}")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

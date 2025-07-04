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
from meutils.caches import rcache

from meutils.decorators.contextmanagers import try_catch, atry_catch

from meutils.apis.baidu.image_enhance import image_enhance

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, HTTPException, Request, status

router = APIRouter()
TAGS = ["图片处理"]


@router.get("/image")
async def enhance(url: str= Query(..., description="图片链接")):
    url = unquote(url)
    return await image_enhance(url)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

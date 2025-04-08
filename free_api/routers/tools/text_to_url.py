#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : text_to_file
# @Time         : 2025/4/8 18:01
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import shortuuid

from meutils.pipe import *
from meutils.oss.minio_oss import Minio
from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header

router = APIRouter()
TAGS = ["text_to_url"]


class Text(BaseModel):
    text: str


@router.post("/text_to_url")
async def create_file(
        request: Text,
):
    data = request.text.encode()
    url = await Minio().upload(data, filename=f'{shortuuid.random()}.txt')

    return {'url': url}


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : check
# @Time         : 2025/8/26 10:49
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import time

from meutils.pipe import *
from meutils.apis.volcengine_apis.videos import get_valid_token

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["sys"]


@router.get("/{biz}")
async def get_user_info(
        biz: str,
        batch_size: Optional[int] = Query(None),
):
    if biz == 'volc':
        if tokens := await get_valid_token(batch_size=batch_size, seed=int(time.time())):
            return {
                'biz': biz,
                'tokens': tokens.split(),
            }

    return {
        'biz': biz,
        'tokens': [],
    }


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/check')

    app.run()

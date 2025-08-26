#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : check
# @Time         : 2025/8/26 10:49
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *

from meutils.apis.oneapi.tasks import polling_tasks, refund_tasks
from meutils.apis.oneapi.user import get_user, get_api_key_log
from meutils.apis.oneapi.channel import ChannelInfo, create_or_update_channel as _create_or_update_channel

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["sys"]


@router.get("/token/{biz}")
async def get_user_info(
        biz: str,
):
    if biz == 'volc':
        pass


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/oneapi')

    app.run()

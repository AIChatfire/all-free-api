#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : extra_api
# @Time         : 2024/9/18 13:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.apis.oneapi.user import get_user, get_api_key_log
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["oneapi"]

get_user_with_cache = alru_cache(ttl=60)(get_user)


@router.get("/token")
async def get_user_info(
        auth: Optional[str] = Depends(get_bearer_token),
        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    api_key = auth

    data = await get_api_key_log(api_key)
    if data and (user_id := data[0]['user_id']):
        if data:= await get_user_with_cache(user_id):
            data['data']['access_token'] = '🔥chatfire'
            return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

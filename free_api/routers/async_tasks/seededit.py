#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : seededit
# @Time         : 2024/12/19 09:07
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.jimeng import images
from meutils.apis.jimeng.files import face_recognize
from meutils.schemas.jimeng_types import FEISHU_URL_MAPPER
from meutils.apis.oneapi.user import get_user_from_api_key

from meutils.config_utils.lark_utils import get_next_token_for_polling

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["图片"]


@router.get("/tasks/{task_id}")
@alru_cache(ttl=30)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    task_response = await images.get_task(task_id, token)
    return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/tasks")
async def create_task(
        request: images.ImageRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    # user_data = await get_user_from_api_key(api_key)
    # token = None
    # if FEISHU_URL := FEISHU_URL_MAPPER.get(str(user_data.get("user_id"))):
    #     token = await get_next_token_for_polling(FEISHU_URL)

    N = 1
    async with ppu_flow(api_key, post="api-images-seededit", n=N):
        task_response = await images.create_task(request)

        await redis_aclient.set(task_response.task_id, task_response.system_fingerprint, ex=7 * 24 * 3600)
        return task_response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


@router.post("/tasks/face_recognize")
async def create_task(
        request: dict,  # image: xxx
        api_key: Optional[str] = Depends(get_bearer_token),
):
    if 'image' in request:
        data = await face_recognize(request.get("image"))
        return data
    else:
        raise HTTPException(status_code=404, detail="Image not found")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

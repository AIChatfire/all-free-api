#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : replicate
# @Time         : 2024/11/15 18:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 可当作通用异步任务接口


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.siliconflow import images
from meutils.schemas.replicate_types import ReplicateRequest, ReplicateResponse

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["异步任务"]


@router.get("/predictions/{task_id}")
@alru_cache(ttl=15)
async def get_task(
        task_id: str,
):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    # task_type = None
    # if "-" in task_id:
    #     task_type, _ = task_id.rsplit("-", 1)  # 区分业务
    #
    # if task_type is None:
    #     pass
    #
    # elif task_type.startswith(TaskType.kling_image):
    #     data = await images.get_task(task_id, token, oss=oss)
    #     return data.model_dump(exclude_none=True, exclude={"system_fingerprint"})

    response = await redis_aclient.get(task_id)
    data = json.loads(response)
    data.pop('system_fingerprint', None)
    return data


@router.post("/models/{provider}/{model}/predictions")
async def create_task(
        provider: str,
        model: str,
        request: ReplicateRequest,

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    # image_response = await images.generate(request.input)
    # url = "https://oss.ffire.cc/files/kling_watermark.png"

    response = ReplicateResponse(input=request.input, output=[])
    await redis_aclient.set(response.id, response.model_dump_json(), ex=7 * 24 * 3600)

    return response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

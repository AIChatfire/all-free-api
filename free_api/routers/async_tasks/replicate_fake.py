#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : replicate
# @Time         : 2024/11/15 18:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 可当作通用异步任务接口
import json

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.siliconflow import images
from meutils.schemas.replicate_types import ReplicateRequest, ReplicateResponse
from meutils.apis.replicateai import raw as replicate

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["异步任务"]


# 数据库获取任务 https://api.chatfire.cn/replicate/v1/predictions/d42c7e90a577bdec0a68797e77a8e0d8

# @router.get("/{path:path}/{task_id}") # 通用
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

    response = ReplicateResponse.model_validate_json(response)
    response.status = "succeeded"

    return response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


# /models/black-forest-labs/flux-1.1-pro/predictions
@router.post("/models/{model:path}/predictions")
async def create_task(
        model: str,
        request: ReplicateRequest,

        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),

):
    api_key = auth and auth.credentials or None

    logger.debug(request.model_dump_json(indent=4))

    provider, model = model.split("/")
    if provider == "stabilityai":
        model = "stabilityai"

    image_request = images.ImageRequest(
        model=model,
        **request.input
    )

    async with ppu_flow(api_key, post=f"api-replicate-{model}"):
        image_response = await images.generate(image_request)
        urls = [i.url for i in image_response.data]

        response = ReplicateResponse(model=model, input=request.input, output=urls)
        await redis_aclient.set(response.id, response.model_dump_json(), ex=7 * 24 * 3600)

        return response.model_dump(exclude_none=True, exclude={"system_fingerprint"})


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()
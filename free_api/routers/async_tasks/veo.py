#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fal_ai
# @Time         : 2025/6/3 17:22
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.llm.openai_utils import ppu_flow, get_payment_times
from meutils.apis.videos import veo

from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["视频"]


@router.get("/tasks/{task_id}")
async def get_task(
        task_id: str,
):
    return await veo.get_task(task_id)


@router.post("/tasks")
async def create_task(
        request: dict,
        api_key: Optional[str] = Depends(get_bearer_token),

        headers: dict = Depends(get_headers),
):

    upstream_api_key = headers.get("upstream-api-key")

    model = request.get("model", "veo3")
    dynamic_model = f"api-{model}"

    async with atry_catch(f"{dynamic_model}", api_key=api_key, callback=send_message, request=request):
        async with ppu_flow(api_key, post=dynamic_model, n=1, dynamic=True):
            return await veo.create_task(request, upstream_api_key)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()


"""
UPSTREAM_API_KEY=

curl -X 'POST' \
  'http://0.0.0.0:8000/veo/v1/tasks' \
  -H "UPSTREAM-API-KEY: $UPSTREAM_API_KEY" \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer sk-iPNbgHSRkQ9VUb6iAcCa7a4539D74255A6462d29619d6519' \
  -H 'Content-Type: application/json' \
  -d '{
        "prompt": "牛飞上天了",
        "model": "veo3",
        "images": [
            "https://filesystem.site/cdn/20250612/VfgB5ubjInVt8sG6rzMppxnu7gEfde.png",
            "https://filesystem.site/cdn/20250612/998IGmUiM2koBGZM3UnZeImbPBNIUL.png"
        ],
        "enhance_prompt": true
    }'

"""
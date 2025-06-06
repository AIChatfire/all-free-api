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
from meutils.apis.fal import tasks as fal_tasks

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["Fal"]

"""
curl --request GET \
  --url https://queue.fal.run/fal-ai/flux-pro/requests/$REQUEST_ID \
  --header "Authorization: Key $FAL_KEY"
"""


@router.get("/fal-ai/{model:path}/requests/{request_id}")  # {task_id:path} 反代有问题
@alru_cache(ttl=30)
async def get_task(
        model: str,
        request_id: str,
):
    return await fal_tasks.get_task(model, request_id)


@router.post("/fal-ai/{model:path}")  # {task_id:path} 反代有问题
async def create_task(
        model: str,
        request: dict,
        api_key: Optional[str] = Depends(get_bearer_token),
):
    """
    计费逻辑设计
    :param model:
    :param request:
    :param api_key:
    :return:
    """
    # N = 0
    N = get_payment_times(request)

    dynamic_model = f"api-{model}"
    if resolution := request.get("resolution"):
        dynamic_model += f"-{resolution}"

    async with atry_catch(f"{dynamic_model}", api_key=api_key, callback=send_message, request=request):
        async with ppu_flow(api_key, post=dynamic_model, n=N, dynamic=True):  # kling-video/v2/master/image-to-video
            return await fal_tasks.create_task(model, request)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

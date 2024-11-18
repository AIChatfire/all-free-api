#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : suno_api
# @Time         : 2024/5/29 15:43
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

import json_repair

from meutils.pipe import *
from meutils.llm.openai_utils import appu, ppu_flow
from meutils.db.redis_db import redis_aclient
from meutils.notice.feishu import send_message as _send_message
from meutils.schemas.suno_types import SunoAIRequest
from meutils.schemas.task_types import TaskType, Task

from meutils.apis.sunoai import suno
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.schemas.suno_types import SunoRequest

from fastapi import APIRouter, File, UploadFile, Query, Form, Header, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter()

send_message = partial(
    _send_message,
    url="https://open.feishu.cn/open-apis/bot/v2/hook/c903e9a7-ece0-4b98-b395-0e1f6a1fb31e",
    title=__name__,
)

TAGS = ["GOAMZ"]


@router.post("/music")
async def create_tasks(
        request: Request,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    request_data = json_repair.loads((await request.body()).decode())
    request_data = {**request_data, **request_data['input']}

    request = SunoAIRequest(**request_data)
    send_message(request)

    async with ppu_flow(api_key, post="api-sunoai-chirp"):
        task = await suno.create_task(request)
        if task and task.status:
            suno.send_message(f"任务提交成功：\n\n{task.id}")

            await redis_aclient.set(task.id, task.system_fingerprint, ex=7 * 24 * 3600)

            response = {
                "code": 200,
                "data": {
                    "task_id": task.id,
                },
                "message": "success"
            }
            return response

        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/music/{task_id}")
async def get_task(
        task_id: str,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    api_key = auth and auth.credentials or None

    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="Task ID not found")

    clips = await suno.get_task(task_id, token)

    response = {
        "code": 200,
        "data": {
            "task_id": task_id,
            "status": f"{clips[0].get('status')}d",  # completed
            "input": str(clips[0].get('metadata')),
            "clips": {clip.get("id"): clip for clip in clips},
        },
        "message": "success"
    }
    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1/goamz')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : volcengine
# @Time         : 2025/5/29 17:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.volcengine_apis import tasks as volcengine_tasks

from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from fastapi import APIRouter, File, UploadFile, Query, Form, Body, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["火山"]

"""
1.
使用 Action=CVSync2AsyncSubmitTask 接口提交任务，获取到 task_id ；
2.
使用 Action=CVSync2AsyncGetResult 接口 通过 task_id 查询任务结果。

"""


@router.post("/{path:path}")
async def generate(
        request: dict = Body(...),
        Action: str = Query(None, description="接口名称"),
        Version: str = Query(None, description="接口版本"),
        api_key: Optional[str] = Depends(get_bearer_token),
):
    if "task_id" in request:
        return await volcengine_tasks.get_task(request)

    else:
        model = request.get("req_key")
        async with ppu_flow(api_key, post=f"api-volcengine-{model}"):
            task_reponse = await volcengine_tasks.create_task(request)

            return task_reponse


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

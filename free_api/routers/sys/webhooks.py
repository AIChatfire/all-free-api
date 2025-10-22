#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : webhook
# @Time         : 2025/10/15 09:30
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import json

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.apis.utils import make_request
from meutils.db.redis_db import redis_aclient
from meutils.str_utils.json_utils import json_path

from meutils.llm.openai_utils import create_chat_completion_chunk
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers

from meutils.schemas.openai_types import CompletionUsage, CompletionRequest, chat_completion, chat_completion_chunk, \
    chat_completion_chunk_stop

from meutils.schemas.image_types import ImageRequest, ImagesResponse

from sse_starlette import EventSourceResponse
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks, \
    Body

router = APIRouter()
TAGS = ["webhooks"]


@router.api_route("/{biz}", methods=["GET", "POST"], tags=TAGS)
async def webhook(
        request: Request,
        biz: str,

        expr: str = Query(None),
        task_id: str = Query(None),
        # event: str = Form(None),
        # user: str = Form(""),
        # file: UploadFile | None = File(None) # todo 兼容 formdata
):
    # ct = request.headers.get("content-type", "")

    if request.method == "GET" and task_id:  # 通用接口
        if (data := await redis_aclient.lrange(f"webhook:{biz}:{task_id}", 0, -1)):
            return json.loads(data[0])
        else:
            raise HTTPException(status_code=404, detail="task_id not found")

    # data = await request.json()
    data = request

    task_id = (
            data.get("id")
            or data.get("task_id")
            or data.get("request_id")
            or data.get("requestId")
    )

    if not task_id and expr and (task_ids := json_path(data, expr)):
        task_id = task_ids[0]

    key = f"webhook:{biz}:{task_id}"
    await redis_aclient.lpush(key, json.dumps(data))
    await redis_aclient.expire(key, 3600)

    # logger.debug(bjson(data))

    # logger.debug(f"webhook: {biz} {task_id} {expr}")
    return data

    # if "application/json" in ct:
    #     data = await request.json()
    #     tid = _save_task(data)
    #     return {"code": 0, "task_id": tid}

    # if any(x in ct for x in ("multipart/form-data", "application/x-www-form-urlencoded")):
    #     payload = {"event": event, "user": user}
    #     if file:
    #         payload["filename"] = file.filename
    #         payload["file_bytes"] = (await file.read()).decode("latin1")
    #     tid = _save_task(payload)
    #     return {"code": 0, "task_id": tid}
    #
    # raise HTTPException(status_code=415, detail="只支持 JSON 或 form-data")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/webhooks')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/7/8 14:27
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from meutils.schemas.wechat_types import Message, HookResponse

from meutils.schemas.vidu_types import ViduRequest
from meutils.apis.vidu import vidu_video

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["HOOK"]


@router.post("/wechat")  # todo: sd3 兜底
async def create_reply(
        request: Message,
):
    logger.debug(request.model_dump_json(indent=4))

    response = []
    flag = request.Content.split(maxsplit=1)[-1]
    if flag.startswith(('/v', '/video')):
        prompt = flag.strip('/video').split('/v')[-1]
        video_request = ViduRequest(prompt=prompt)
        task = await vidu_video.create_task(video_request)

        for i in range(16):
            await asyncio.sleep(5)
            try:
                data = await vidu_video.get_task(task.id, task.system_fingerprint)
                if data.get("state") == "success":
                    video_url = data.get("creations")[0].get("uri")
                    response = [HookResponse(type='video', content=video_url)]
                    break
            except Exception as e:
                logger.debug(e)

    return response


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

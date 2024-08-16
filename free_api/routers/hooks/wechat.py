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

from meutils.apis.vidu import vidu_video
from meutils.schemas.vidu_types import ViduRequest

from meutils.apis.siliconflow.flux import create_image
from meutils.schemas.openai_types import ImageRequest

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["HOOK"]


@router.post("/wechat")  # todo: sd3 兜底，增加 key
async def create_reply(
        request: Message,
):
    logger.debug(request.model_dump_json(indent=4))

    responses = []
    content = request.Content.split(maxsplit=1)[-1]
    if content.startswith(('/v', '/video')):
        prompt = content.strip('/video').split('/v')[-1]
        video_request = ViduRequest(prompt=prompt)
        task = await vidu_video.create_task(video_request)

        for i in range(16):
            await asyncio.sleep(5)
            try:
                data = await vidu_video.get_task(task.id, task.system_fingerprint)
                if data.get("state") == "success":
                    video_url = data.get("creations")[0].get("uri")
                    responses += [HookResponse(content=f"任务已完成🎉🎉🎉\nTaskId: {task.id}")]
                    responses += [HookResponse(type='video', content=video_url)]
                    break
            except Exception as e:
                logger.debug(e)
                responses = [HookResponse(content=str(e))]

    elif content.startswith(('/flux-pro')):
        prompts = content.replace('/flux-pro', '').strip().split(maxsplit=1)
        if len(prompts) > 1:
            aspect_ratio, prompt = prompts
        else:
            prompt = prompts[0]

        image_reponse = await create_image(ImageRequest(prompt=prompt))
        responses = [HookResponse(type='image', content=img.url) for img in image_reponse.data]

    return responses


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

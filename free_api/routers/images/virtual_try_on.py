#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : virtual_try_on
# @Time         : 2024/10/24 19:55
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.llm.openai_utils import ppu_flow

from meutils.apis.hf import kolors_virtual_try_on

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["Images"]


@router.post("/images/virtual-try-on")  # todo: sd3 兜底
async def generate(
        request: kolors_virtual_try_on.KolorsTryOnRequest,
        api_key: Optional[str] = Depends(get_bearer_token),
):

    logger.debug(request.model_dump_json(indent=4))
    # return await text_to_image.create(request)

    logger.debug(request)
    async with ppu_flow(api_key, post="api-kolors-virtual-try-on"):
        data = await kolors_virtual_try_on.create(request)
        return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

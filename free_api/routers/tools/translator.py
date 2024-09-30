#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : translator
# @Time         : 2024/7/18 14:19
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.schemas.translator_types import DeeplxRequest
from meutils.apis.translator import deeplx

from meutils.llm.openai_utils import ppu_flow

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header

router = APIRouter()
TAGS = ["Translator"]


@router.post("/translator")
async def translate(
        request: DeeplxRequest,
        auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
):
    # logger.debug(request.model_dump_json(indent=4))

    api_key = auth and auth.credentials or None

    async with ppu_flow(api_key, post="api-translator"):
        data = await deeplx.translate(request)
        return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()



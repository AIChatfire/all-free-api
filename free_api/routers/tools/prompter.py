#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : prompts
# @Time         : 2024/7/17 17:21
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : beautify_prompts


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.kuaishou import klingai_video
from meutils.config_utils.lark_utils import get_next_token_for_polling

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header

router = APIRouter()
TAGS = ["提示词优化"]


@router.get("/prompter")
async def beautify_prompt(
        prompt: str = Query("一直带有雄鹰翅膀的老虎，飞翔在大海上方"),
):
    return {}


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

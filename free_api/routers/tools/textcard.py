#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : textcard
# @Time         : 2024/9/14 09:46
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://xy.siliconflow.cn/
# https://xy.siliconflow.cn/api/sensitive?word=996


from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials
from meutils.llm.openai_utils import ppu_flow
from meutils.apis.kuaishou import klingai_video
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.apis.jina import rerank
from meutils.llm.prompts import TEXT_CARD

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header
from fastapi.responses import HTMLResponse

router = APIRouter()
TAGS = ["汉语新解"]

payload = {
    "messages": [
        {
            "role": "user",
            "content": TEXT_CARD
        }
    ],
    "chat_id": "eqI1A0z",
    "model": "Pro/THUDM/glm-4-9b-chat",
    "temperature": 0.7,
    "top_k": 50,
    "top_p": 0.7,
    "max_tokens": 4096,
    "frequency_penalty": 0
}


@router.get("/textcard")
async def beautify_prompt(
        prompt: str = Query("一直带有雄鹰翅膀的老虎，飞翔在大海上方"),
):
    html_content = open('templates/textcard.html', 'r', encoding='utf-8').read()
    return HTMLResponse(content=html_content, status_code=200)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

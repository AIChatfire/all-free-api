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

from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header
from fastapi.responses import HTMLResponse

router = APIRouter()
TAGS = ["HTML"]


@router.get("/render/{file:path}")
@alru_cache()
async def render(
        file: str,
):
    if Path(file).is_file():
        html_content = Path(file).read_text()
        return HTMLResponse(content=html_content)


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v1')

    app.run()

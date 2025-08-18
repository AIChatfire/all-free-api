#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : health
# @Time         : 2025/8/18 13:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from fastapi import APIRouter

router = APIRouter()
TAGS = ["health"]


@router.api_route("")
async def health_check():
    return {"status": "ok"}


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    # app = App(lifespan=nacos_lifespan)
    app = App()

    app.include_router(router, '/health')

    app.run()

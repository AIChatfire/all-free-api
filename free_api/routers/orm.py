#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : orm
# @Time         : 2024/11/20 12:03
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 基础操作 https://mp.weixin.qq.com/s/nbYhmkN05eqnvjGFvzMbXQ


from meutils.pipe import *
from meutils.schemas.db.oneapi_types import Hero, Tasks
from meutils.db.orm import AsyncSession, get_session, update_or_insert

from meutils.serving.fastapi.dependencies.auth import get_bearer_token, HTTPAuthorizationCredentials

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

router = APIRouter()
TAGS = ["空服务"]


@router.api_route("/v1/{id:path}", methods=["GET", "POST"])
async def create_request(
        id: str,
        session: AsyncSession = Depends(get_session),
):
    if task := await session.get(Tasks, id):
        task.finish_time = int(time.time())

        await session.commit()
        await session.refresh(task)
        return task


@router.api_route("/v2/{ident:path}", methods=["GET", "POST"])
async def create_request(
        ident: str,

        backgroundtasks: BackgroundTasks = BackgroundTasks,
):
    ident = {
        "task_id": 'test',
    }

    def update_fn(entity):
        logger.debug(entity)
        entity.status = "SUCCESS"
        entity.finish_time = int(time.time())

    backgroundtasks.add_task(update_or_insert, Tasks, ident, update_fn)

    return


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/v0')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")

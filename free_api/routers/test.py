#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : free
# @Time         : 2024/11/6 18:14
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 空服务调试

from meutils.pipe import *
from meutils.serving.fastapi.dependencies.auth import get_bearer_token
from meutils.serving.fastapi.dependencies.headers import get_headers

from meutils.decorators.contextmanagers import try_catch

# from meutils.serving.fastapi.lifespans import nacos_lifespan

from fastapi import APIRouter, Body, File, UploadFile, Header, Query, Form, Depends, Request, HTTPException, status, \
    BackgroundTasks

router = APIRouter()
TAGS = ["空服务"]


class H(BaseModel):
    reasoning_stream: bool


@router.api_route("/error", methods=["GET"])
async def create_request(
        status_code: Optional[int] = Query(None),
        detail: Optional[str] = Query("xx"),
):
    if status_code:
        raise HTTPException(status_code=status_code, detail=detail)
    else:
        raise Exception(
            f"{status_code}: {detail}"
        )
    # raise HTTPException(status_code=status_code, detail=f"Not Implemented: {status_code}")


@router.api_route("/{path:path}", methods=["GET", "POST"])
async def create_request(
        path: str,
        request: Request,
        # request: dict = Body(...),

        api_key: Optional[str] = Depends(get_bearer_token),

        headers: dict = Depends(get_headers),

        reasoning_stream: bool = Header(True),

):
    # with try_catch(__name__, payload=payload):
    #     1 / 0

    # try:
    #     1/0
    # except Exception as e:
    #     logger.exception(e)
    #     raise

    logger.debug(bjson(headers))
    logger.debug(request.method)
    logger.debug(request.headers)
    logger.debug(request.url)

    logger.debug(api_key)
    logger.debug(path)

    logger.debug(reasoning_stream)

    logger.debug(request.headers.get('H'))
    logger.debug(request.headers.get('user-agent'))

    params = request.query_params._dict

    payload = {}
    try:
        payload = await request.json()
    except Exception as e:
        form_data = (await request.form())._dict
        logger.debug(form_data)

        logger.debug((await request.form()).multi_items())
        # {'oss': UploadFile(filename='202507若悟-工资表.xlsx', size=17512, headers=Headers({
        #                                                                                       'content-disposition': 'form-data; name="oss"; filename="202507è\x8b¥æ\x82\x9f-å·¥èµ\x84è¡¨.xlsx"; filename*=UTF-8\'\'202507%E8%8B%A5%E6%82%9F-%E5%B7%A5%E8%B5%84%E8%A1%A8.xlsx',
        #                                                                                       'content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})),
        #  'a': 'xxx'}

    form = (await request.form())._dict

    data = {
        "id": "test",
        "status": "SUBMITTED",
        "headers": dict(request.headers),
        "url": str(request.url),
        "method": request.method,
        "path": path,
        "payload": payload,
        "form": form,
        "params": params,

        "x-headers": headers.get("x-headers"),

        **params
    }
    if isinstance(payload, dict):
        data.update(payload)

    logger.debug(bjson(data))

    return data


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    # app = App(lifespan=nacos_lifespan)
    app = App()

    app.include_router(router, '/v1')

    app.run()

    os.getenv("OPENAI_API_KEY_OPENAI")

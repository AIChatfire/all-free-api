#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : elevenlabs
# @Time         : 2025/7/14 16:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.decorators.contextmanagers import atry_catch
from meutils.notice.feishu import send_message_for_dynamic_router as send_message

from meutils.apis.utils import make_request_httpx

from meutils.apis.oneapi.user import get_user_money
from meutils.llm.openai_utils.billing_utils import get_billing_n, billing_for_async_task, billing_for_tokens
from meutils.io.files_utils import to_url, get_file_duration, to_bytes
from meutils.serving.fastapi.dependencies import get_bearer_token, get_headers
from meutils.serving.fastapi.dependencies.auth import parse_token

from meutils.serving.fastapi.dependencies.auth import get_bearer_token

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, status, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from starlette.datastructures import UploadFile

router = APIRouter()
TAGS = ["Audio"]


# https://api.elevenlabs.io/v1/text-to-speech/voice_id/with-timestamps
# "https://api.elevenlabs.io/v1/text-to-speech/:voice_id"
@router.post("/v1/{path:path}")
async def text_to_speech(
        request: Request,

        path: str,

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),

):
    # 跳过计费
    is_free = True if headers.get("x-free") else False

    upstream_base_url = headers.get('upstream_base_url') or "https://api.elevenlabs.io"
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    # params
    params = dict(request.query_params)

    # form_data
    prompt_tokens = 0
    data = files = None
    payload = {}
    # logger.debug((await request.form()).multi_items())

    if data := (await request.form())._dict:
        file = data.get("file")

        if isinstance(file, UploadFile):
            file: UploadFile = data.pop("file", None)

            content = file.file.read()
            files = {"file": (file.filename, content)}
        else:
            content = await to_bytes(file)
            files = {"file": ('_.mp3', content)}
        prompt_tokens = await get_file_duration(filename='.mp3', content=content) * 1000
    else:  # payload
        payload = await request.json()

    # model
    model = payload.get("model_id") or data.get("model_id")

    logger.debug(bjson(payload))
    logger.debug(data)

    # 计费
    prompt_tokens = prompt_tokens or len(payload.get("text", "").encode())

    logger.debug(f"prompt_tokens: {prompt_tokens}")

    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": 0,
        "total_tokens": prompt_tokens
    }

    headers = {"xi-api-key": upstream_api_key}
    async with atry_catch(f"{path}", api_key=api_key, callback=send_message,
                          upstream_base_url=upstream_base_url, upstream_path=path, request={**payload, **data}):

        # 检查余额
        if not is_free and (user_money := await get_user_money(api_key)):
            if user_money < 1:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足")

        data = await make_request_httpx(
            base_url=upstream_base_url,
            path=f"/v1/{path}",
            payload=payload,
            params=params,
            data=data,
            files=files,
            headers=headers,

            debug=True

        )

        # 计费
        n = 1 if prompt_tokens == 0 else None
        not is_free and await billing_for_tokens(model=f"elevenlabs/{model}", api_key=api_key, usage=usage, n=n)

        if isinstance(data, dict): return data

        data = data.content
        if payload.get("response_format") == "url":
            url = await to_url(data, filename=f'{shortuuid.random()}.mp3')
            return {"audio": url}

        return StreamingResponse([data], media_type="audio/mpeg")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/elevenlabs')

    app.run()

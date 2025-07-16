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
TAGS = ["Minimax", "Audio"]


@router.post("/v1/{path:path}")
async def text_to_speech(
        request: Request,

        path: str,

        api_key: Optional[str] = Depends(get_bearer_token),
        headers: dict = Depends(get_headers),

):
    upstream_base_url = headers.get('upstream_base_url') or "https://api.minimaxi.com/v1"
    upstream_api_key = headers.get('upstream_api_key')  # 上游号池管理
    upstream_api_key = await parse_token(upstream_api_key)

    group_id, upstream_api_key = upstream_api_key.split('|')  # 特殊处理

    # params
    params = dict(request.query_params)
    params = {"GroupId": group_id}

    # form_data
    prompt_tokens = 0
    files = None
    payload = {}
    # logger.debug((await request.form()).multi_items())

    if data := (await request.form())._dict:
        if file := data.get("file"):
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
    model = payload.get("model", path)
    task_id = model

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

    headers = {"Authorization": f"Bearer {upstream_api_key}"}
    async with atry_catch(f"{path}", api_key=api_key, callback=send_message,
                          upstream_base_url=upstream_base_url, upstream_path=path, request={**payload, **data}):

        # 检查余额
        if user_money := await get_user_money(api_key):
            if user_money < 1:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="余额不足")

        data = await make_request_httpx(
            base_url=upstream_base_url,
            path=path,
            payload=payload,
            params=params,
            data=data,
            files=files,
            headers=headers,

            debug=True

        )

        # 计费
        n = 1 if prompt_tokens == 0 else None
        model = f"minimax/{model}" if 'files' not in path else "api-oss"
        await billing_for_tokens(model=model, api_key=api_key, usage=usage, n=n, task_id=task_id)

        if isinstance(data, dict):
            if payload.get("response_format") == "url" and (audio := data.get("data", {}).get("audio")):
                data["data"]["audio"] = await to_url(bytes.fromhex(audio), filename=f'{shortuuid.random()}.mp3')

            logger.debug(data)

            return data

        return StreamingResponse([data], media_type="audio/mpeg")


if __name__ == '__main__':
    from meutils.serving.fastapi import App

    app = App()

    app.include_router(router, '/minimax')

    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : step
# @Time         : 2024/6/19 09:00
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://yuewen.cn/chats/new
import time

import httpx

from meutils.pipe import *

from meutils.schemas.step_types import BASE_URL, PASSPORT_REGISTER_DEVICE, API_CREATE_CHAT, API_CHAT
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.llm.openai_utils import create_chat_completion_chunk, create_chat_completion, token_encoder
from meutils.llm.utils import oneturn2multiturn


@alru_cache(ttl=180 - 3)
async def refresh_token(token):
    headers = {
        'oasis-token': token,
        'oasis-appid': '10200',
        'oasis-platform': 'web',
        'oasis-webid': '23f3eabc7d0779a948c50293dd1510cbc06302a9',
        'priority': 'u=1, i',
        'x-waf-client-type': 'fetch_sdk',
        'content-type': 'application/json',
        'connect-protocol-version': '1',
    }
    payload = {}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        response = await client.post(PASSPORT_REGISTER_DEVICE, json=payload)

        logger.debug(response.text)  # "device":{"platform":"web","deviceID":"f6c832c5577ece3629101ed7b3a7cd24951522f2"}

        if response.is_success:
            data = response.json()
            access_token = data.get("accessToken").get("raw")
            refresh_token = data.get("refreshToken").get("raw")
            device_id = data.get("device").get("deviceID")

            return {
                **headers,
                "oasis-token": f"{access_token}...{refresh_token}",
                "oasis-webid": device_id
            }


async def create_chat(token):
    headers = await refresh_token(token)

    payload = {
        "chatName": "新话题"
    }
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        response = await client.post(API_CREATE_CHAT, json=payload)

        # logger.debug(response.text)  # "device":{"platform":"web","deviceID":"f6c832c5577ece3629101ed7b3a7cd24951522f2"}

        # return response.is_success and response.json()
        return response.json()


async def create(token, chat_id='114658351650275328', prompt='1+1'):
    headers = await refresh_token(token)
    headers = {**headers, 'content-type': 'application/connect+json'}  # 缓存会被就地改变，必须copy

    payload = {
        "chatId": chat_id,
        "messageInfo"
        : {"text": prompt, "author": {"role": "user"}},
        "messageMode": "SEND_MESSAGE"
    }

    # todo: 请求体在变化
    payload = f"""\u0000\u0000\u0000\u0000r{json.dumps(payload, ensure_ascii=False)}""".replace(' ', '')
    # payload = f"""\u0000\u0000\u0000\u0000s{json.dumps(payload, ensure_ascii=False)}""".replace(' ', '')

    chunk_pattern = re.compile(r'{"textEvent":{"text":"(.*?)"}}')

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=100) as client:
        async with client.stream("POST", API_CHAT, content=payload) as response:
            if response.is_success:
                async for chunk in response.aiter_lines():
                    for content in chunk_pattern.findall(chunk):
                        yield content
                        # logger.debug(content)

    # async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=100) as client:
    #     async with client.stream("POST", API_CHAT, content=payload_2) as response:
    #         if response.is_success:
    #             async for chunk in response.aiter_lines():
    #                 for content in chunk_pattern.findall(chunk):
    #                     yield content


class Completions(object):

    def __init__(self, api_key):
        self.api_key = api_key

    async def acreate(self, request: ChatCompletionRequest):
        # {'chatId': '114654967119589376', 'chatName': '新话题'}
        chat_id = request.conversation_id or (await create_chat(self.api_key)).get("chatId")

        prompt = request.last_content
        # prompt = oneturn2multiturn(request.messages)  # 模拟多轮对话

        logger.debug(prompt)
        logger.debug(chat_id)

        _ = create(self.api_key, chat_id=chat_id, prompt=prompt)

        return create_chat_completion_chunk(_, chat_id)  # 可以继续上个id问答


if __name__ == '__main__':
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmF0ZWQiOnRydWUsImFnZSI6MjEsImJhbmVkIjpmYWxzZSwiY3JlYXRlX2F0IjoxNzE4NzcwMzMxLCJleHAiOjE3MTg3NzIxMzEsIm1vZGUiOjIsIm9hc2lzX2lkIjo4MzU0NzEyNzUwMjAxMjQxNiwidmVyc2lvbiI6Mn0.IrBcFq6EP3viilCE-oQ0rahQTB3m_MH_o29dOUrXs-8...eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOjEwMjAwLCJkZXZpY2VfaWQiOiJkOGMzZmQyMDNiMDVkZDYyNWRhMjE0NzExZmZmYTc1YjM2YWUzMDIzIiwiZXhwIjoxNzIwOTE5NDAxLCJvYXNpc19pZCI6ODM1NDcxMjc1MDIwMTI0MTYsInBsYXRmb3JtIjoid2ViIiwidmVyc2lvbiI6Mn0.DOucHDLLquvRvynk1MczqUEHvQE6tfuAINXAnY2qBgQ"
    # TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmF0ZWQiOnRydWUsImFnZSI6MSwiYmFuZWQiOmZhbHNlLCJleHAiOjE3MTMyNTc4NzgsIm1vZGUiOjIsIm9hc2lzX2lkIjo5MTQ0NzQ3MzEwODg3NzMxMiwidmVyc2lvbiI6MX0.sWF3D2Aspbbyc9KMv8XYLTX_NZcrCDe_T_KXctgirS0...eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOjEwMjAwLCJkZXZpY2VfaWQiOiJlOTAwZTdjZDU1ZmM4Y2ZlOTMwYTdiYTVhZjZkY2ViMTdjNzdlYTNlIiwiZXhwIjoxNzE0NTUyMDc4LCJvYXNpc19pZCI6OTE0NDc0NzMxMDg4NzczMTIsInZlcnNpb24iOjF9.HmtZ66ITi9N4uwPhDE5ob9ASN2MwzcT1pDeihvi5TdI"
    # accessToken: 需要保活
    # headers = arun(refresh_token(token))
    # print(headers)

    # TOKEN = arun(refresh_token(TOKEN))
    # print(TOKEN)

    # print(arun(create_chat(token)))
    # time.sleep(20)
    # print(arun(create_chat(token)))
    chat_id = arun(create_chat(token))

    print(arun(create(token, prompt="1+1")))

    # for i in async2sync_generator(Completions(token).acreate(ChatCompletionRequest())):
    #     print(i)

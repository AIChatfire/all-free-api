#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : yuanbao
# @Time         : 2024/6/11 18:56
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.yuanbao_types import SSEData, BASE_URL, API_CHAT, API_GENERATE_ID, API_DELETE_CONV, GET_AGENT_CHAT
from meutils.llm.openai_utils import create_chat_completion_chunk, create_chat_completion
from meutils.llm.utils import oneturn2multiturn


# import rev_HunYuan


class Completions(object):
    def __init__(self, api_key: str):
        self.api_key = api_key

        self.httpx_client = httpx.Client(
            base_url=BASE_URL,
            cookies=self.cookies,
            follow_redirects=True,
            timeout=300
        )
        self.httpx_aclient = httpx.AsyncClient(
            base_url=BASE_URL,
            cookies=self.cookies,
            follow_redirects=True,
            timeout=300
        )

    async def acreate(self, request: ChatCompletionRequest):

        prompt = oneturn2multiturn(request.messages)

        # logger.debug(prompt)

        chunks = self.achat(prompt)

        if request.stream:
            return create_chat_completion_chunk(chunks, redirect_model=request.model)
        else:
            content = ""
            prompt_tokens = 1
            async for chunk in chunks:
                content += chunk
                prompt_tokens += 1

            return create_chat_completion(content, redirect_model=request.model)

    @cached_property
    def cookies(self):
        hy_user, hy_token, sensorsdata2015jssdkcross = self.api_key.split('|')

        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

        cookies = {
            'web_uid': f'{uuid.uuid4()}',
            'hy_user': hy_user,
            'hy_token': hy_token,
            'hy_source': 'web',
            'sensorsdata2015jssdkcross': sensorsdata2015jssdkcross,
        }

        return cookies

    def chat(self, prompt: str = '1+1'):
        payload = {
            "prompt": prompt,

            # "model": "gpt_175B_0404",
            # "plugin": "Adaptive",
            # "displayPrompt": "1+1",
            # "displayPromptType": 1,
            # "options": {},
            # "multimedia": [],
            # "agentId": "naQivTmsDa",
            # "version": "v2"
        }
        with self.httpx_client.stream(method="POST", url=f"{API_CHAT}/xxx", json=payload) as response:
            for chunk in response.iter_lines():
                # print(chunk)
                print(SSEData(chunk=chunk, crop_image=False).content)

    async def achat(self, prompt: str = '1+1', chatid: Optional[str] = None):
        payload = {
            "prompt": prompt,

            # "model": "gpt_175B_0404",
            # "plugin": "Adaptive",
            # "displayPrompt": "1+1",
            # "displayPromptType": 1,
            # "options": {},
            # "multimedia": [],
            # "agentId": "naQivTmsDa",
            # "version": "v2"
        }

        chatid = chatid or uuid.uuid4()

        async with self.httpx_aclient.stream(method="POST", url=f"{API_CHAT}/{chatid}", json=payload) as response:
            async for chunk in response.aiter_lines():
                content = SSEData(chunk=chunk, crop_image=True).content
                # print(content)
                yield content

    def generate_id(self, random: bool = True):
        if random:
            return f'{uuid.uuid4()}'
        return self.httpx_client.post(API_GENERATE_ID).text

    def delete_conv(self, chatid):
        response = self.httpx_client.post(f"{API_DELETE_CONV}/{chatid}")
        return response.status_code == 200


# data = '{"model":"gpt_175B_0404","prompt":"1+1","plugin":"Adaptive","displayPrompt":"1+1","displayPromptType":1,"options":{},"multimedia":[],"agentId":"naQivTmsDa","version":"v2"}'

#
# payload = {"model": "gpt_175B_0404", "prompt": "画条可爱的狗", "plugin": "Adaptive", "displayPrompt": "画条可爱的狗",
#            "displayPromptType": 1, "options": {}, "multimedia": [], "agentId": "naQivTmsDa", "version": "v2"}
# # payload = {"model":"gpt_175B_0404","prompt":"搜索下今天的新闻","plugin":"Adaptive"}
#
# chatid = generate_id()
# #
# chatid = 'gtcnTp5C1G'
# chatid = "xx"
# url = f'https://yuanbao.tencent.com/api/chat/{chatid}'
#
# #
# with httpx.stream("POST", url, json=payload, headers=headers, cookies=cookies) as response:
#     for chunk in response.iter_lines():
#         # print(chunk)
#         print(SSEData(chunk=chunk, crop_image=False).content)


if __name__ == '__main__':
    api_key = "bUZenNkB3YaXTbw9|lTb5OHLVMWugG/U9/hzmYbzP09T1d3VcrQ5wqtYIDQObyUVrVFBOTayWg9uNWtFS|%7B%22distinct_id%22%3A%22100000458739%22%2C%22first_id%22%3A%2218b12e46a2cc31-0422341cefa2bb-18525634-2073600-18b12e46a2d16e0%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_utm_medium%22%3A%22cpc%22%2C%22%24search_keyword_id%22%3A%22dfc6144d0063998d000000026667e3ec%22%2C%22%24search_keyword_id_type%22%3A%22baidu_seo_keyword_id%22%2C%22%24search_keyword_id_hash%22%3A5499731361824189%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThiMTJlNDZhMmNjMzEtMDQyMjM0MWNlZmEyYmItMTg1MjU2MzQtMjA3MzYwMC0xOGIxMmU0NmEyZDE2ZTAiLCIkaWRlbnRpdHlfbG9naW5faWQiOiIxMDAwMDA0NTg3MzkifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22100000458739%22%7D%2C%22%24device_id%22%3A%2218b12e46a2cc31-0422341cefa2bb-18525634-2073600-18b12e46a2d16e0%22%7D"
    # chatid = generate_id()
    # print(chatid)
    # print(delete_conv(chatid))
    # payload = {
    #     # "model": "gpt_175B_0404",
    #     # "prompt": "1+1",
    #     "prompt": "错了",
    #
    #     # "plugin": "Adaptive",
    #     # "displayPrompt": "1+1",
    #     # "displayPromptType": 1,
    #     # "options": {},
    #     # "multimedia": [],
    #     # "agentId": "naQivTmsDa",
    #     # "version": "v2"
    # }
    # chat(payload)

    async2sync_generator(Completions(api_key).achat('画条狗')) | xprint

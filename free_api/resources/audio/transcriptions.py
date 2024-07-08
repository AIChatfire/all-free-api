#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : transcriptions
# @Time         : 2024/7/5 09:12
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.schemas.openai_types import AudioRequest
from meutils.notice.feishu import send_message as _send_message

from openai import OpenAI, AsyncOpenAI, APIStatusError

from free_api.resources.completions.polling_openai import Completions

send_message = partial(
    _send_message,
    url="https://open.feishu.cn/open-apis/bot/v2/hook/e0db85db-0daf-4250-9131-a98d19b909a9",
    title="轮询api-keys"
)


class Transcriptions(Completions):

    async def create(self, **kwargs):

        client: Optional[AsyncOpenAI] = None
        for i in range(5):  # 轮询个数
            try:
                api_key = await self.get_next_api_key()
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=self.base_url,
                )

                # client.audio.speech.create(**kwargs)
                return await client.audio.transcriptions.create(**kwargs)

            except APIStatusError as e:
                logger.error(e)

                if e.status_code == 400:
                    send_message(f"{e.response}\n\n{e}\n\n{request.model_dump()}", title=self.base_url)

                if i > 3:  # 兜底策略
                    send_message(f"{client and client.api_key}\n\n轮询{i}次\n\n{e}\n\n{self.feishu_url}",
                                 title=self.base_url)

        return


if __name__ == '__main__':
    file = open("/Users/betterme/PycharmProjects/AI/ChatLLM/examples/openaisdk/demo.mp3", 'rb')
    # request = AudioRequest(file=file.read())
    # print(request.model_dump(exclude_none=True))

    client = AsyncOpenAI(
        # base_url="https://apis.chatfire.cn/v1",
        # api_key="sk-tfoO5ew6EIK9WbMlE7A5012832274593912e3e79De734198"
    )

    print(arun(Transcriptions(client).create(file=file, model='whisper-large-v3')))

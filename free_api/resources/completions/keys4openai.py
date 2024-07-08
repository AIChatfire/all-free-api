#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : keys4openai
# @Time         : 2024/5/14 16:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://github.com/CZT0/StableOpenAI/tree/main
"""
1. 如果有需要增加tokens计算，可放大
2. 平滑+前后置内容
3. 淘汰策略+轮询策略
    前置淘汰
    后置淘汰：根据具体错误
4. 统计信息
5. 日志监控
"""
import functools
import os

from meutils.pipe import *
from meutils.config_utils.lark_utils import get_spreadsheet_values
from meutils.notice.feishu import send_message
from meutils.db.redis_db import redis_aclient

from chatllm.schemas.openai_api_protocol import ChatCompletionRequest
from openai import AsyncOpenAI, OpenAI

import redis


# np.random.choice()

class PollKeys(object):  # 轮询

    def __init__(self, provider='kimi', rpm: int = 3):
        self.provider = provider
        self.base_url = f"https://any2chat.chatfire.cn/{self.provider}"
        self.delay = 60 // rpm
        self.redis_key = f"api-provider:{provider}"

    async def acreate(self, request: ChatCompletionRequest):
        for i in range(3):  # 轮询个数
            api_key = self.api_key

            try:
                completion = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=api_key,
                ).chat.completions.create(**request.model_dump())

                return await completion

            except Exception as e:
                await redis_aclient.hincrby(self.redis_key, api_key, 1)  # 错误计数
                # todo：次数超过阈值，淘汰
                api_key_counter = await redis_aclient.hgetall(self.redis_key)

                logger.error(e)
                send_message(f"{api_key_counter.decode()}: {e}", title=self.provider)

    @property
    async def api_key(self):
        """获取一个api_key"""
        while 1:
            api_key = await redis_aclient.lpop(self.provider)
            await redis_aclient.rpush(self.provider, api_key)

            return api_key

    @diskcache(location='check_api_key_cache', ttl=15 * 60, ignore=['self'])
    async def check_api_key(self, api_key):
        """后台定时检测：半小时检测一遍
        1、被禁用
        2、无余额

        """
        logger.debug("@@@@@@@@2")
        payload = {
            "token": api_key  # "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."
        }
        response = httpx.Client(base_url=self.base_url).post("/token/check", json=payload)
        _ = response.json()

        # 淘汰key发出警告
        message = f"{api_key}: {_}"
        logger.warning(message)
        send_message(message, title=f"{self.provider}_check_api_key")

        return _.get("live", False)

    def get_and_update_api_keys(self):  # 保活
        """定时更新&空闲更新
                1、 通过飞书更新keys
                2、检测key
                3、更新key


                调用 => key有效性检查 => 当前key `60 // rpm +1` s后，放入keys右侧 => 轮询
                """
        # 获取
        logger.debug(feishu_url := os.getenv(f"{self.provider.upper()}_KEYS_URL", "DEEPSEEK_KEYS_URL"))

        df = get_spreadsheet_values(
            feishu_url=feishu_url,
            to_dataframe=True)
        api_keys = filter(None, df[0])
        api_keys = filter(self.check_api_key, api_keys)

        # 更新
        self.redis_client.delete(self.provider)
        self.redis_client.rpush(self.provider, *api_keys)

        return api_keys


if __name__ == '__main__':
    print(str(PollKeys().check_api_key('')))

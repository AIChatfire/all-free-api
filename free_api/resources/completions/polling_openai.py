#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : multi_key_openai
# @Time         : 2024/5/22 14:16
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.notice.feishu import send_message as _send_message
from meutils.db.redis_db import redis_client, redis_aclient
from meutils.config_utils.lark_utils import aget_spreadsheet_values

from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache
from meutils.schemas.openai_types import chat_completion, chat_completion_chunk, ChatCompletionRequest, CompletionUsage

from openai import OpenAI, AsyncOpenAI, APIStatusError

send_message = partial(
    _send_message,
    url="https://open.feishu.cn/open-apis/bot/v2/hook/e0db85db-0daf-4250-9131-a98d19b909a9",
    title=__name__
)

redis_client.decode_responses = True


class Completions(object):
    def __init__(
            self,
            base_url: Optional[str] = None,
            api_key: Optional[str] = None,
            feishu_url: Optional[str] = None,
            redis_key: Optional[str] = None
    ):
        self.base_url = base_url  # from urllib.parse import quote, unquote
        self.api_key = api_key
        self.feishu_url = feishu_url
        self.redis_key = redis_key

    async def acreate(self, request: ChatCompletionRequest):
        data = to_openai_completion_params(request)
        if 'gemini' in request.model:
            data.pop("extra_body", None)

        client: Optional[AsyncOpenAI] = None
        for i in range(5):  # 轮询个数
            try:
                api_key = await self.get_next_api_key()
                logger.debug(api_key)
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=self.base_url,
                    default_headers={"X-Failover-Enabled": "true"},
                )
                completion = await client.chat.completions.create(**data)
                if completion:
                    return self.calculate_tokens(request, completion)  ####### todo重构
                else:
                    send_message(f"{request}\n\ncompletion: {completion}", title=f"completion is str 很奇怪")

            except APIStatusError as e:  # {'detail': 'Insufficient Balance'}
                logger.error(e)
                # e.code=='1210' # {'error': {'code': '1210', 'message': 'API 调用参数有误，请检查文档。'}}

                if e.status_code == 400:  # todo: 细分错误
                    send_message(f"{e.response}\n\n{e}\n\n{request.model_dump()}", title=self.base_url)

                    # Error
                    # code: 429 - {'error': {
                    #     'message': 'Your account cog830hkqq4ttrgnvpfg【ak-eria54hskes111c9t6ji】 request reached max request: 3, please try again after 1 seconds',
                    #     'type': 'rate_limit_reached_error'}}

                    if any(i in str(e) for i in {
                        "The parameter is invalid",
                        "'role' has invalid value",
                        "角色信息不能为空",  # 智谱
                        "'assistant' must not be empty",  # moonshot
                    }):
                        data['messages'] = [{'role': 'user', 'content': str(request.messages)}]  # 重构 messages
                        continue
                    elif "max_tokens: Must be less than" in str(e):
                        data['max_tokens'] = 4096
                        continue

                    elif "Model disabled" in str(e):
                        send_message(f"Model disabled：{data['model']}", title=self.base_url)

                        data['model'] = "Qwen/Qwen2.5-7B-Instruct"
                        continue

                    else:
                        chat_completion.choices[0].message.content = chat_completion_chunk.choices[
                            0].delta.content = str(e)
                        return [chat_completion_chunk] if request.stream else chat_completion

                if i > 3:  # 兜底策略
                    send_message(f"{client and client.api_key}\n\n轮询{i}次\n\n{e}\n\n{self.feishu_url}",
                                 title=self.base_url)

        return [chat_completion_chunk] if request.stream else chat_completion

    async def get_next_api_key(self):
        if self.redis_key:  # 优先轮询 redis里的 keys
            api_key = await redis_aclient.lpop(self.redis_key)
            if api_key:
                api_key = api_key.decode()  # b""

                await redis_aclient.rpush(self.redis_key, api_key)
            else:
                send_message(f"redis_key为空，请检查\n\n{self.redis_key}")

            return api_key

        if self.feishu_url:  # 轮询飞书里的 keys
            api_keys = (await aget_spreadsheet_values(feishu_url=self.feishu_url, to_dataframe=True))[0]
            api_keys = [k for k in api_keys if k]  # 过滤空值

        else:
            api_keys = self.api_key.split(',')  # 轮询请求体里的 keys

        api_key = np.random.choice(api_keys)  # 随机轮询
        return api_key

    @staticmethod
    def calculate_tokens(request: ChatCompletionRequest, completion, alfa: float = 1.02):

        if request.stream or isinstance(completion, str) or not (completion.choices and completion.choices[0].message):
            return completion

        # 非流&一般逆向api需要重新计算
        if completion.usage is None or (completion.usage and completion.usage.completion_tokens == 1):
            prompt_tokens = len(token_encoder_with_cache(str(request.messages)))
            completion_tokens = len(token_encoder_with_cache(str(completion)))

            prompt_tokens = int(alfa * prompt_tokens)
            completion_tokens = int(alfa * completion_tokens)
            total_tokens = prompt_tokens + completion_tokens

            completion.usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

        completion.object = "chat.completion"
        return completion


if __name__ == '__main__':
    pass
    print(arun(Completions().acreate(
        ChatCompletionRequest(model='deepseek-chat', messages=[{"role": "user", "content": "你是谁"}])
    )))

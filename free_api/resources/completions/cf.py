#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : cf
# @Time         : 2024/4/30 13:32
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import shortuuid

from meutils.pipe import *
from meutils.notice.feishu import send_message
from meutils.str_utils import chinese_convert
from meutils.ai_audio.utils import to_audio
from meutils.oss.minio_oss import Minio
from asgiref.sync import sync_to_async, async_to_sync
from meutils.llm.openai_utils import create_chat_completion_chunk, create_chat_completion

from chatllm.schemas.openai_types import chat_completion, chat_completion_chunk as _chat_completion_chunk
from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, UsageInfo

from chatllm.llmchain.completions import chatglm_web
from fastapi import UploadFile, File


class Completions(object):
    def __init__(self, api_key: Optional[str] = None):  # @cf/bytedance/stable-diffusion-xl-lightning
        """CLOUDFLARE_ACCOUNT_ID-CLOUDFLARE_API_TOKEN"""

        api_key = api_key or os.getenv("CLOUDFLARE_API_TOKEN")
        cloudflare_account_id, api_key = api_key.split('-', maxsplit=1)

        base_url = f"https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/ai/run/"

        headers = {"Authorization": f"Bearer {api_key}"}

        self.httpx_client = httpx.Client(base_url=base_url, follow_redirects=True, timeout=100, headers=headers)
        self.httpx_aclient = httpx.AsyncClient(base_url=base_url, follow_redirects=True, timeout=100, headers=headers)

    async def acreate(self, request: ChatCompletionRequest):  # todo: minio 兜底
        payload = {
            "prompt": request.last_content
            # "prompt": deeplx.translate(request.last_content).get('data')
        }

        response: httpx.Response = await self.httpx_aclient.post(request.model, json=payload)

        logger.debug(response.headers)
        if response.status_code != 200:
            send_message(response.text, title='cf')
            response.raise_for_status()

        # main
        file_object = await chatglm_web.Completions().put_object_for_openai(response.content, "")
        image_url = file_object.filename

        # # 预生成
        # file_id = "file_id.png"
        # background_tasks.add_task(
        #     Minio().put_object_for_openai,
        #     response.content, bucket_name="tmp", prefix="sd", file_id=file_id
        # )
        # image_url = f"https://oss.chatfire.cn/tmp/sd/{file_id}"

        chunk = f"![{request.model}]({image_url})"

        # Path('debug.png').write_bytes(response.content) # debug

        if request.stream:
            chat_completion_chunk = _chat_completion_chunk.model_copy(deep=True)

            # 前置
            chat_completion_chunk.choices[0].delta.content = chunk
            yield chat_completion_chunk

            # 结束标识
            chat_completion_chunk.choices[0].delta.content = ""
            chat_completion_chunk.choices[0].finish_reason = "stop"
            yield chat_completion_chunk

        else:
            chat_completion.usage.completion_tokens = 1
            chat_completion.choices[0].message.content = chunk
            yield chat_completion

    async def acreate_(self, request: ChatCompletionRequest):  # todo: minio 兜底
        payload = {
            "prompt": request.last_content
            # "prompt": deeplx.translate(request.last_content).get('data')
        }

        response: httpx.Response = await self.httpx_aclient.post(request.model, json=payload)

        logger.debug(response.headers)
        if response.status_code != 200:
            send_message(response.text, title='cf')
            response.raise_for_status()

        # main
        file_object = await chatglm_web.Completions().put_object_for_openai(response.content, "")
        image_url = file_object.filename

        chunk = f"![{request.model}]({image_url})"

        # Path('debug.png').write_bytes(response.content) # debug

        if request.stream:
            chat_completion_chunk = _chat_completion_chunk.model_copy(deep=True)

            # 前置
            chat_completion_chunk.choices[0].delta.content = chunk
            yield chat_completion_chunk

            # 结束标识
            chat_completion_chunk.choices[0].delta.content = ""
            chat_completion_chunk.choices[0].finish_reason = "stop"
            yield chat_completion_chunk

        else:
            chat_completion.usage.completion_tokens = 1
            chat_completion.choices[0].message.content = chunk
            yield chat_completion

    async def acreate_asr(
        self,
        file: Union[UploadFile] = File(...),  # 文件链接
    ):
        # 强制转换为mp3
        tmp_filename = f"{shortuuid.random()}.mp3"
        with open(tmp_filename, 'wb') as f:
            f.write(file.file.read())

        os.system(f"ffmpeg -i {tmp_filename} {tmp_filename}.mp3 -y")

        payload = {"file": (tmp_filename, open(f"{tmp_filename}.mp3", 'rb'))}
        response: httpx.Response = await self.httpx_aclient.post("@cf/openai/whisper", files=payload)

        if response.status_code != 200:
            send_message(response.text, title='cf asr')
            response.raise_for_status()

        _ = response.json().get("result", {"text": ""})
        # logger.debug(_)

        # pip install opencc opencc-python-reimplemented
        _ = json.loads(chinese_convert(json.dumps(_, ensure_ascii=False)))

        # logger.debug(_)

        return _


if __name__ == '__main__':
    request = ChatCompletionRequest(
        model='/@cf/bytedance/stable-diffusion-xl-lightning',
        messages=[{'role': 'user', 'content': '画一条可爱的猫'}],
        stream=True
    )


    async def f():
        async for i in Completions().acreate(request):
            print(i)


    # response = Completions().acreate(request)
    print(arun(f()))
    #
    # for i in Completions().create(request):
    #     print(i)

    # import tiktoken
    #
    # print(tiktoken.get_encoding('cl100k_base').encode('我是谁'))

    import openai

    # openai.OpenAI.chat.completions.create()


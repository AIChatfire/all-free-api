#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : suno
# @Time         : 2024/6/25 09:41
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import httpx
import jsonpath
import json_repair

from meutils.pipe import *
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.schemas.suno_types import SunoAIRequest
from meutils.apis.sunoai import suno
from meutils.config_utils.lark_utils import get_next_token_for_polling

template = """


- 自动歌词懒人模式
```
gpt_description_prompt: 写首中国风的歌曲
```

- 自定义歌词模式(每行逗号分割)
```
mv: chirp-v3-5,
title: "这里是歌词标题",
prompt: "这里是你的自定义歌词：吧啦吧啦"
```

- 官网的标准模式(json结构)
```json
{
    "prompt": "",
    "gpt_description_prompt": "写首中国风的歌曲",
    "title": "",
    "tags": "",
    "continue_at": null,
    "continue_clip_id": null,
    "infill_start_s": null,
    "infill_end_s": null,
    "make_instrumental": false,
    "mv": "chirp-v3-5"
}
```
"""


class Completions(object):

    def __init__(self, api_key):
        self.api_key = api_key

    async def create(self, request: ChatCompletionRequest):
        token = await get_next_token_for_polling(suno.FEISHU_URL)

        if "chat" in request.model:
            request = SunoAIRequest(gpt_description_prompt=request.last_content)

        else:
            data = json_repair.repair_json(f"{{{request.last_content}}}", return_objects=True)
            if isinstance(data, dict) and data:
                request = SunoAIRequest(**data)
            else:
                return f"请按照规定格式提交任务（未知错误联系管理员）\n\n {template}"

        task = await suno.create_task(request, token)
        return create_chunks(task.id, token)


def music_info(df):
    """
    #   'audio_url': 'https://cdn1.suno.ai/63c85335-d8ec-4e17-882a-e51c2f358b2d.mp3',
    #   'video_url': 'https://cdn1.suno.ai/25c7e34b-6986-4f7c-a5f2-537dd80e370c.mp4',
    # https://cdn1.suno.ai/image_bea09d9e-be4a-4c27-a0bf-67c4a92d6e16.png
    :param df:
    :return:
    """
    df['🎵音乐链接'] = df['id'].map(
        lambda x: f"**请两分钟后试听**[🎧音频](https://cdn1.suno.ai/{x}.mp3)[▶️视频](https://cdn1.suno.ai/{x}.mp4)"
    )
    # todo: 图片链接发生变化
    df['专辑图'] = df['id'].map(lambda x: f"![🖼](https://cdn1.suno.ai/image_{x}.jpeg)")  # _large

    df_ = df[["id", "created_at", "model_name", "🎵音乐链接", "专辑图"]]

    return f"""
🎵 **「{df['title'][0]}」**

`风格: {df['tags'][0]}`

```toml
{df['prompt'][0]}
```


{df_.to_markdown(index=False).replace('|:-', '|-').replace('-:|', '-|')}
    """


async def create_chunks(task_id, token):
    clip_ids = task_id.split("suno-", 1)[-1].split(",")

    yield "✅开始生成音乐\n\n"
    await asyncio.sleep(1)

    yield f"音乐ID：\n"
    for clip_id in clip_ids:
        yield f"- [{clip_id}](https://cdn1.suno.ai/{clip_id}.mp3)\n\n"
        await asyncio.sleep(1)

    yield f"""[🔥音乐进度]("""
    await asyncio.sleep(1)

    for i in range(100):
        await asyncio.sleep(1) if i < 10 else await asyncio.sleep(3)

        # 监听歌曲
        clips = await suno.get_task(task_id, token)

        STATUS = {"streaming", "complete", "error"}  # submitted queued streaming complete/error
        if all(clip.get('status') in STATUS for clip in clips):  # 可提前返回
            yield f"""{'🎵' if i % 2 else '🔥'}"""
        else:
            yield f""") ✅\n\n"""
            df = pd.DataFrame(clips)
            df['tags'] = [clip.get('metadata').get('tags') for clip in clips]
            df['prompt'] = [clip.get('metadata').get('prompt') for clip in clips]
            md_string = music_info(df)
            yield md_string  # yield from
            break

    else:
        yield "长时间未获取或者中断，可从超链接获取音乐"


if __name__ == '__main__':
    print(arun(get_suno_task("4a41481e-6002-48fb-8e84-469214653bcd")))

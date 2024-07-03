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

    async def acreate(self, request: ChatCompletionRequest):

        if "chat" in request.model:
            payload = SunoAIRequest(gpt_description_prompt=request.last_content).model_dump()
            task_info = await generate_music(self.api_key, payload)
            return create_chunks(task_info)

        data = json_repair.repair_json(f"{{{request.last_content}}}", return_objects=True)
        if isinstance(data, dict) and data:
            payload = SunoAIRequest(**data).model_dump()
            task_info = await generate_music(self.api_key, payload)  # 阻塞执行，奇怪？
            return create_chunks(task_info)

        return f"请按照规定格式提交任务（未知错误联系管理员）\n\n {template}"


async def generate_music(api_key, payload):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    async with httpx.AsyncClient(base_url="https://api.chatfire.cn/task", headers=headers, timeout=30) as client:
        task_info = await client.post("/suno/v1/generation", json=payload)
        return task_info.is_success and task_info.json()


async def get_suno_task(task_id):
    api_key = "api_key"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    async with httpx.AsyncClient(base_url="https://api.chatfire.cn/task", headers=headers, timeout=30) as client:
        task_info = await client.get(f"/suno/v1/tasks/{task_id}")
        if task_info.is_success:
            return task_info.json()


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
    df['专辑图'] = df['id'].map(lambda x: f"![🖼](https://cdn1.suno.ai/image_{x}.png)")  # _large

    df_ = df[["id", "created_at", "model_name", "🎵音乐链接", "专辑图"]]

    return f"""
🎵 **「{df['title'][0]}」**

`风格: {df['tags'][0]}`

```toml
{df['prompt'][0]}
```


{df_.to_markdown(index=False).replace('|:-', '|-').replace('-:|', '-|')}
    """


async def create_chunks(task_info):
    task_id = task_info.get('id', 'task_id')
    music_ids = jsonpath.jsonpath(task_info, "$.clips..id") | xjoin(',')

    yield "✅开始生成音乐\n\n"

    await asyncio.sleep(3)
    yield f"任务ID：\n- [{task_id}](https://api.chatfire.cn/task/suno/v1/tasks/{task_id})\n\n"

    await asyncio.sleep(3)
    yield f"音乐ID：\n"
    for music_id in music_ids.split(","):
        yield f"- [{music_id}](https://api.chatfire.cn/task/suno/v1/music/{music_id})\n\n"

    await asyncio.sleep(3)
    yield f"""[🔥音乐进度]("""

    for i in range(100):
        await asyncio.sleep(1) if i < 10 else await asyncio.sleep(3)

        # 监听歌曲
        clips = (await get_suno_task(task_id)) or []

        STATUS = {"streaming", "complete", "error"}  # submitted queued streaming complete/error
        if all(clip in STATUS for clip in clips):  # 可提前返回
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

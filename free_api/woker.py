from meutils.pipe import *
from openai import OpenAI

base_url = 'https://openai.chatfire.cn/tools/textcard/v1'
messages = [
    {
        "content": "996",
        "role": "user"
    }
]
r = OpenAI(base_url=base_url).chat.completions.create(
    messages=messages,
    model=''
)

# .choices[0].message.content

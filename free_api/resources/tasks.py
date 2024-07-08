#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : tasks
# @Time         : 2024/7/5 15:22
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 异步任务获取、文件内容获取、常用信息等等等
import shortuuid

# POST: 创建任务 https://api.chatfire.cn/tasks
# GET: 获取任务 https://api.chatfire.cn/tasks/{task_id}


from meutils.pipe import *


class TaskRequest(BaseModel):
    task_type: str  # 任务类型: suno、tts
    purpose: str  # 任务用途: 翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译、总结、问答、写作、总结、翻译
    task_id: Optional[str] = None
    task_name: Optional[str] = None

    task_status: str  # 任务状态: pending、running、finished、failed
    task_result: str  # 任务结果

    task_params: dict = {}

    # task_log: str  # 任务日志

    extra_body: dict = {}

    # 自动生成task_id?提交的时候就生成

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.task_id = self.task_id or f"{self.task_type}-{shortuuid.random()}"

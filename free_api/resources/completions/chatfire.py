#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chatfire
# @Time         : 2024/7/3 13:13
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


OpenAI

class Completions(object):

    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, request: ChatCompletionRequest):
        request.messages
        request.last_content

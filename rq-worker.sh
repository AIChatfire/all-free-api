#!/usr/bin/env bash
# @Project      : AI @by PyCharm
# @Time         : 2024/7/11 16:08
# @Author       : betterme
# @Email        : 313303303@qq.com
# @Software     : PyCharm
# @Description  :

python -m rq.cli worker default --with-scheduler -v --url $REDIS_URL
#python -m rq.cli worker default high normal low --with-scheduler -v --url $REDIS_URL

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : demo
# @Time         : 2024/5/14 17:00
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import json

import redis
# import time
#
# # 连接到 Redis
# r = redis.Redis(host='localhost', port=6379, db=0)
#
# # 初始 API keys 列表
# api_keys = ["key1", "key2", "key3", "key4"]
#
#
# keys = r.lrange('api_keys', 0, -1)
# # print(keys)
#
# print(r.rpush("keys11", *api_keys))
# keys = r.lrange('keys11', 0, -1)
# print(keys)
#
# # 将 API keys 存入 Redis 列表
# r.delete('api_keys')  # 删除旧的 keys 列表
# for key in api_keys:
#     r.rpush('api_keys', key)
#
# def check_api_key(api_key):
#     # 这里应实现实际的 API key 检查逻辑
#     # 返回 True 表示 key 有效，False 表示 key 无效
#     # 示例中，假设 "key3" 是无效的
#     return api_key != "key3"
#
# def poll_api_keys():
#     while True:
#         # 获取所有 API keys
#         keys = r.lrange('api_keys', 0, -1)
#         keys = [key.decode('utf-8') for key in keys]
#         # 检查并淘汰无效的 keys
#         valid_keys = []
#         for key in keys:
#             if check_api_key(key):
#                 valid_keys.append(key)
#
#         print(valid_keys)
#
#
#         # 更新 Redis 列表
#         r.delete('api_keys')
#         for key in valid_keys:
#             r.rpush('api_keys', key)
#
#         # 模拟轮询间隔
#         time.sleep(10)
#
# # 启动轮询
# poll_api_keys()


# from meutils.pipe import *
# import redis
# import schedule
# import time
# import asyncio
#
# # 连接到 Redis
# r = redis.Redis(host='localhost', port=6379, db=0)
#
#
# # 假设我们有一个方法来获取新的 API keys
# def fetch_new_api_keys():
#     # 此处模拟获取新的 API keys 的过程
#     return ["key1", "key2", "key3"]
#
#
# # 定时更新 API keys 的方法
# def update_api_keys():
#     new_keys = fetch_new_api_keys()
#     r.delete('api_keys')  # 删除旧的 keys
#     for key in new_keys:
#         r.rpush('api_keys', key)  # 添加新的 keys
#
#
# # 定时任务，设置每小时更新一次 API keys
# schedule.every().hour.do(update_api_keys)
#
#
# # 检查 API key 是否有效的函数
# def check_api_key(api_key):
#     # 模拟检查过程
#     # 真实场景下可以是一个 HTTP 请求，检查返回的状态码
#     return api_key != "key2"  # 假设 key2 是无效的
#
#
# # 异步轮询 API keys 的方法
# async def poll_api_keys():
#     while True:
#         keys = r.lrange('api_keys', 0, -1)
#         for key in keys:
#             key_str = key.decode('utf-8')
#             if not check_api_key(key_str):
#                 await r.lrem('api_keys', 0, key)  # 移除无效的 key
#                 print(f"Removed invalid key: {key_str}")
#         await asyncio.sleep(60)  # 每分钟轮询一次
#
#
# # 主函数，启动所有任务
# def main():
#     # 启动定时任务的线程
#     def run_schedule():
#         while True:
#             schedule.run_pending()
#             time.sleep(1)
#
#     # 启动异步轮询任务
#     loop = asyncio.get_event_loop()
#     loop.create_task(poll_api_keys())
#
#     # 启动定时任务
#     import threading
#     schedule_thread = threading.Thread(target=run_schedule)
#     schedule_thread.start()
#
#     # 保持主线程运行
#     loop.run_forever()
#
#
# if __name__ == '__main__':
#     main()



import redis

# 连接到Redis服务器
client = redis.StrictRedis(host='localhost', port=6379, db=0)

# 定义API Key和Redis键
api_key = "api_key_1"
redis_key = "api_call_count"

# 记录API Key的调用
client.hincrby(redis_key, api_key, 1)
client.hincrby(redis_key, api_key+"_", 1)

# 查询API Key的调用次数
count = client.hget(redis_key, api_key)
print(f"{api_key} has been called {count} times.")

print(client.hgetall(redis_key))


client.lrem("api_keys", 0, api_key)

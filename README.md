**# 商业版联系313303303

- 兼容Openai、Oneapi、Newapi等系统
- 支持国产所有大模型转Openai接口
- 多账号轮询
- 动态维护账号池、api-key池、token池等
- 高并发，横向扩容
- 预警通知



```shell
docker run -d --name=all-free-api -p 8080:8080 \
  --log-driver json-file \
  --log-opt max-size=1m \
  --log-opt max-file=10
```
#!/usr/bin/env bash
# @Project      : AI @by PyCharm
# @Time         : 2025/9/18 19:34
# @Author       : betterme
# @Email        : 313303303@qq.com
# @Software     : PyCharm
# @Description  :

#
ntpdate cn.pool.ntp.org

# 清空docker日志
truncate -s 0 /var/lib/docker/containers/*/*-json.log

# 显示当前所有镜像echo "当前所有镜像如下："docker images

# 显示当前所有镜像
echo "当前所有镜像如下："
docker images

# 删除无标签的镜像（即 <none>:<none> 的镜像）
echo "正在删除无标签的镜像..."
docker images -f "dangling=true" -q | xargs -r docker rmi

# 删除未被容器使用的镜像（谨慎操作，可能会删除一些你认为有用的镜像）
echo "正在删除未被容器使用的镜像..."
docker image prune -a -f

echo "清理完成！"

# autoheal
docker rm -f autoheal && docker run -d \
  --name autoheal \
  --restart always \
  -e TZ=Asia/Shanghai \
  -e AUTOHEAL_CONTAINER_LABEL=all \
  -v /var/run/docker.sock:/var/run/docker.sock \
  willfarrell/autoheal



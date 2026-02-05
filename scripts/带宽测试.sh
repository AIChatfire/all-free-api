#!/usr/bin/env bash
# @Project      : AI @by PyCharm
# @Time         : 2026/2/4 10:52
# @Author       : betterme
# @Email        : 313303303@qq.com
# @Software     : PyCharm
# @Description  :


# 最常用的一键测试脚本
wget -qO- bench.sh | bash

# 或安装 speedtest-cli 后测试
apt install speedtest-cli -y  # Debian/Ubuntu
#yum install speedtest-cli -y  # CentOS/RHEL
speedtest-cli
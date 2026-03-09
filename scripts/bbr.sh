#!/usr/bin/env bash
# @Project      : AI @by PyCharm
# @Time         : 2026/2/26 16:29
# @Author       : betterme
# @Email        : 313303303@qq.com
# @Software     : PyCharm
# @Description  :
sudo bash -c 'cat > /etc/sysctl.d/99-custom-network-tuning.conf << EOF
# ==========================================
# 1. 开启 BBR 拥塞控制算法 (极大提升跨国高延迟吞吐量)
# ==========================================
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# ==========================================
# 2. TCP 长连接 (KeepAlive) 与超时优化
# 减少无用连接占用，提升长连接的保活效率
# ==========================================
# 缩短 TCP KeepAlive 发送探测包的时间间隔（默认两小时太长，这里改为 10 分钟）
net.ipv4.tcp_keepalive_time = 600
# 探测包发送间隔
net.ipv4.tcp_keepalive_intvl = 30
# 探测失败多少次后断开
net.ipv4.tcp_keepalive_probes = 5
# 缩短 TIME_WAIT 状态的等待时间，加速端口回收
net.ipv4.tcp_fin_timeout = 15
# 允许重用 TIME_WAIT 状态的 socket（对高并发短连接有效）
net.ipv4.tcp_tw_reuse = 1

# ==========================================
# 3. 开启 TCP Fast Open (TFO)
# 允许在 TCP 握手期间发送数据，直接减少 1-RTT 延迟
# ==========================================
# 3 表示同时开启客户端和服务端的 TFO 支持
net.ipv4.tcp_fastopen = 3

# ==========================================
# 4. UDP 缓冲区优化 (为 QUIC / HTTP/3 核心优化)
# QUIC 基于 UDP，Linux 默认的 UDP 缓存太小，会导致高延迟下丢包降速
# ==========================================
# 最大接收缓冲区大小 (推荐 2.5MB 以上，这里设为 4MB)
net.core.rmem_max = 4194304
# 最大发送缓冲区大小
net.core.wmem_max = 4194304

# ==========================================
# 5. 其他高并发防丢包优化
# ==========================================
# 增大全连接队列
net.core.somaxconn = 65535
# 增大半连接队列
net.ipv4.tcp_max_syn_backlog = 65535

# 增大系统级最大文件描述符数
fs.file-max = 1000000

EOF'


# 使上述配置立即生效
sudo sysctl --system

lsmod | grep bbr




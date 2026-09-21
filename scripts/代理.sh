#!/usr/bin/env bash
# @Project      : AI @by PyCharm
# @Time         : 2026/9/1 16:12
# @Author       : betterme
# @Email        : 313303303@qq.com
# @Software     : PyCharm
# @Description  :
#!/bin/bash
# ============================================
# Ubuntu Dante SOCKS5 代理一键安装脚本
# 绑定指定 IP: 110.42.51.240
# 端口: 1080
# 认证: 用户名/密码
# ============================================

set -e

# ---------- 配置区 ----------
PROXY_IP="64.81.112.31"
PROXY_PORT="1080"
PROXY_USER="chatfire"
PROXY_PASS="chatfirechatfire"  # 随机生成密码，也可改成你自己固定的
# ---------------------------

echo "=========================================="
echo "  开始安装 Dante SOCKS5 代理"
echo "  绑定 IP: ${PROXY_IP}"
echo "  端口: ${PROXY_PORT}"
echo "=========================================="

# 1. 安装 dante-server
echo "[1/6] 安装 dante-server ..."
apt-get update -y
apt-get install -y dante-server

# 2. 备份原配置
echo "[2/6] 备份原配置 ..."
if [ -f /etc/danted.conf ]; then
    mv /etc/danted.conf /etc/danted.conf.bak.$(date +%s)
fi

# 3. 写入配置（绑定指定IP，用户名认证）
echo "[3/6] 写入 danted.conf ..."
cat > /etc/danted.conf <<EOF
logoutput: /var/log/danted.log
errorlog: /var/log/danted.error.log

# 监听地址：只接受发往 110.42.51.240:1080 的连接
internal: ${PROXY_IP} port = ${PROXY_PORT}

# 出口地址：所有代理流量从 110.42.51.240 发出
external: ${PROXY_IP}

# 权限用户
user.privileged: root
user.notprivileged: nobody
user.libwrap: nobody

# 认证方式
clientmethod: none
socksmethod: username

# 客户端规则：谁可以连进来
client pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: connect disconnect
}

client block {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: connect error
}

# SOCKS 规则：允许代理的请求
socks pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    command: bind connect udpassociate
    log: connect disconnect
    socksmethod: username
}

socks block {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: connect error
}
EOF

# 4. 创建代理用户（系统用户，用于 SOCKS5 认证）
echo "[4/6] 创建认证用户: ${PROXY_USER} ..."
if id "${PROXY_USER}" &>/dev/null; then
    echo "    用户已存在，仅修改密码"
fi
useradd -r -s /bin/false ${PROXY_USER} 2>/dev/null || true
echo "${PROXY_USER}:${PROXY_PASS}" | chpasswd

# 5. 防火墙放行（ufw / iptables）
echo "[5/6] 配置防火墙 ..."
if command -v ufw &>/dev/null; then
    ufw allow ${PROXY_PORT}/tcp comment 'SOCKS5 Proxy' || true
    echo "    ufw 已放行端口 ${PROXY_PORT}"
else
    # 无 ufw 时尝试 iptables
    iptables -I INPUT -p tcp --dport ${PROXY_PORT} -j ACCEPT 2>/dev/null || true
    echo "    iptables 已放行端口 ${PROXY_PORT}"
fi

# 6. 启动服务
echo "[6/6] 启动 Dante 服务 ..."
mkdir -p /var/log
touch /var/log/danted.log /var/log/danted.error.log

# 先停止旧进程
systemctl stop danted 2>/dev/null || true
killall danted 2>/dev/null || true

# 启动
systemctl daemon-reload
systemctl enable danted
systemctl start danted

sleep 2

# 检查状态
if systemctl is-active --quiet danted; then
    echo ""
    echo "=========================================="
    echo "  ✅ Dante SOCKS5 代理启动成功"
    echo "=========================================="
    echo "  代理地址: ${PROXY_IP}:${PROXY_PORT}"
    echo "  用户名:   ${PROXY_USER}"
    echo "  密码:     ${PROXY_PASS}"
    echo ""
    echo "  测试命令:"
    echo "  curl -x socks5://${PROXY_USER}:${PROXY_PASS}@${PROXY_IP}:${PROXY_PORT} http://httpbin.org/ip"
    echo ""
else
    echo "  ❌ 启动失败，查看日志:"
    echo "  journalctl -u danted -n 50"
    exit 1
fi

# 显示监听状态
echo "  当前监听:"
netstat -tlnp 2>/dev/null | grep ${PROXY_PORT} || ss -tlnp | grep ${PROXY_PORT}
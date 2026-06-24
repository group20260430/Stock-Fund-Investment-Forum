#!/bin/bash
# ============================================================================
# 一键部署脚本 — Stock Fund Investment Forum
# 在 VPS 上以 root 身份执行
# ============================================================================
set -euo pipefail

# ── 配置 ──────────────────────────────────────────────────────
APP_DIR="/opt/Stock-Fund-Investment-Forum"
BACKEND_DIR="${APP_DIR}/backend"
REPO_URL="https://github.com/group20260430/Stock-Fund-Investment-Forum.git"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Stock Fund Investment Forum — 生产环境部署             ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ─ 1. 拉取代码 ─
if [ -d "$APP_DIR" ]; then
    echo "[1/6] 更新已有代码..."
    cd "$APP_DIR"
    git pull origin master
else
    echo "[1/6] 克隆仓库..."
    git clone "$REPO_URL" "$APP_DIR"
fi

# ─ 2. 初始化数据库 ─
echo "[2/6] 检查 MySQL 数据库..."
if ! mysql -u forum_user -p"${MYSQL_PASSWORD:-}" -e "USE stock_fund_forum;" 2>/dev/null; then
    echo "  创建数据库并导入 schema + seed..."
    mysql -u root -p"${MYSQL_ROOT_PASSWORD:-}" < "${APP_DIR}/database/schema.sql"
    mysql -u root -p"${MYSQL_ROOT_PASSWORD:-}" <<SQL
CREATE USER IF NOT EXISTS 'forum_user'@'localhost'
  IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON stock_fund_forum.* TO 'forum_user'@'localhost';
FLUSH PRIVILEGES;
SQL
    mysql -u forum_user -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE:-stock_fund_forum}" < "${APP_DIR}/database/seed.sql"
    echo "  数据库初始化完成"
else
    echo "  数据库已存在，跳过初始化"
fi

# ─ 3. 配置后端环境 ─
echo "[3/6] 配置 Python 虚拟环境..."
cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "  ⚠ 请先配置 $BACKEND_DIR/.env 文件"
    cp "$BACKEND_DIR/.env.production" "$BACKEND_DIR/.env"
    echo "  已从 .env.production 创建 .env，请编辑后重新运行此脚本"
    exit 1
fi

# ─ 4. 安装 systemd 服务 ─
echo "[4/6] 安装 systemd 服务..."
cp "${APP_DIR}/deploy/stock-forum-api.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable stock-forum-api
systemctl restart stock-forum-api
echo "  systemd 服务已启动"

# ─ 5. 配置 Cloudflare Tunnel ─
echo "[5/6] 检查 Cloudflare Tunnel..."
if ! command -v cloudflared &>/dev/null; then
    echo "  安装 cloudflared..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
        -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
fi

echo "  ⚠ 如果尚未创建 Tunnel，请运行:"
echo "    cloudflared tunnel login"
echo "    cloudflared tunnel create stock-forum-api"
echo "    cloudflared tunnel route dns stock-forum-api api.你的域名.com"
echo "  然后编辑 /root/.cloudflared/config.yml 替换隧道 UUID"
echo "  最后: systemctl restart cloudflared"

# ─ 6. 完成 ─
echo "[6/6] 部署完成 ✓"
echo ""
echo "  API 健康检查: http://127.0.0.1:8000/api/health"
echo "  systemd 日志:  journalctl -u stock-forum-api -f"
echo "  Tunnel 日志:  journalctl -u cloudflared -f"

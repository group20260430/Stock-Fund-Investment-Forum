# 软件安装文档

> 项目：股票基金投资论坛 (Stock Fund Investment Forum)
> 版本：v1.2
> 最后更新：2026年6月25日

---

## 一、环境要求

### 1.1 后端

| 依赖 | 版本要求 |
|------|---------|
| Python | >= 3.10 |
| pip | >= 21.0 |
| SQLite | 内置（开发用） |
| MySQL | >= 8.0（生产用，可选） |

### 1.2 前端

| 依赖 | 版本要求 |
|------|---------|
| Node.js | >= 18 |
| npm | >= 9 |

### 1.3 操作系统

- Windows 10/11 ✅（已测试）
- Linux / macOS（理论兼容）

---

## 二、后端安装

### 2.1 克隆仓库

```bash
git clone https://github.com/kkk431/Stock-Fund-Investment-Forum.git
cd Stock-Fund-Investment-Forum
```

### 2.2 创建虚拟环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 包含的主要依赖：

```
fastapi>=0.109.0
uvicorn[standard]
sqlalchemy>=2.0
pydantic>=2.0
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
httpx
python-multipart
aiosmtplib
```

### 2.4 配置环境变量

复制 `.env.example` 为 `.env`（或直接编辑 `.env`），主要配置项：

```env
# 数据库（默认 SQLite）
DATABASE_URL=sqlite:///./stock_fund_forum.db

# JWT 密钥
JWT_SECRET=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=2
REFRESH_TOKEN_EXPIRE_DAYS=7

# SMTP（邮箱验证，留空=开发模式）
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# 管理员初始化账号
ADMIN_PHONE=13800000000
ADMIN_PASSWORD=your-admin-password
ADMIN_NICKNAME=系统管理员

# OAuth 开发模式（无需真实 APP ID）
OAUTH_DEV_MODE=True
```

### 2.5 启动后端

```bash
# 确保在 backend 目录下
uvicorn app.main:app --port 8000 --reload
```

启动后：
- API 服务：`http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`
- 数据库自动创建（SQLite），包含初始板块分类和演示数据

---

## 三、前端安装

### 3.1 安装依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 3.2 配置 API 地址

默认连接 `http://localhost:8000/api`。如需修改，在 `frontend/.env` 中设置：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3.3 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:5173/` 进入论坛首页。

### 3.4 生产构建

```bash
npm run build
npm run preview
```

构建产物输出到 `frontend/dist/` 目录。

---

## 四、数据库初始化

### 4.1 开发环境（SQLite）

后端首次启动时自动完成：
1. 创建 SQLite 数据库文件 `stock_fund_forum.db`
2. 根据 SQLAlchemy ORM 模型自动创建所有表
3. 种子管理员账号（配置在 `.env` 中）
4. 种子初始板块分类（4大分区 + 17个子分类）
5. 种子演示帖子和用户

### 4.2 生产环境（MySQL）

```bash
# 1. 创建数据库
mysql -u root -p -e "CREATE DATABASE stock_fund_forum CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 导入 schema
mysql -u root -p stock_fund_forum < database/schema.sql

# 3. 导入种子数据（可选）
mysql -u root -p stock_fund_forum < database/seed.sql

# 4. 修改 .env 中的数据库连接
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/stock_fund_forum?charset=utf8mb4
```

### 4.3 数据库表结构

| 模块 | 表 | 说明 |
|------|-----|------|
| 用户系统 | users, oauth_accounts, verification_codes, certifications, professional_certifications, risk_assessments, refresh_tokens | 7表 |
| 内容系统 | categories, posts, comments, post_tags, attachments, likes, favorites, favorite_folders, shares, vote_options, vote_records | 11表 |
| 社交系统 | follows, starred_users, groups, group_members, group_posts, messages | 6表 |
| 运营管理 | reports, review_logs, ban_records, sensitive_words, compliance_rules, user_activity_log | 6表 |
| 通知统计 | notifications, points_history, daily_stats | 3表 |

完整 SQL 脚本见 `database/schema.sql`。

---

## 五、运行测试

### 5.1 单元测试

```bash
cd backend
python -m pytest tests/unit/ -v
```

### 5.2 接口测试

```bash
cd backend
python -m pytest tests/run_backend_tests.py
```

或单独运行：

```bash
cd backend
python tests/test_auth_api.py
python tests/test_email_auth_api.py
python tests/test_oauth_api.py
# ... 等 18 个测试脚本
```

### 5.3 测试结果

```
单元测试: 215 passed
接口测试: 18 个文件全部通过
功能测试: 全部通过
总计: ~534 用例，通过率 100%
```

---

## 六、功能限制说明

### 6.1 第三方登录（QQ/微信/微博）

**当前状态：** 开发/测试模式（Dev Mode）模拟运行。

**原因：** 第三方 OAuth 登录在生产环境中需要：
1. 注册企业主体（营业执照）
2. 完成工信部 ICP 备案（域名备案）
3. 完成公安联网备案（公安网监）
4. 在各开放平台创建应用并提交企业资质审核
5. 审核通过后获取 AppID 和 AppSecret

**Dev Mode 原理：**
- 后端配置 `OAUTH_DEV_MODE=True`（默认开启，无需任何第三方凭证）
- 点击 QQ/微信/微博登录按钮时，浏览器直接跳转到模拟回调 URL
- 后端使用预设的 mock 用户资料创建账号，签发 JWT Token
- 前端 `OAuthCallback.vue` 解析 fragment 中的 Token 完成登录
- 完整业务流程可演示，无需任何企业资质

**生产部署时补充配置：**
```env
OAUTH_DEV_MODE=False
QQ_OAUTH_APP_ID=your_app_id
QQ_OAUTH_APP_KEY=your_app_key
WECHAT_OAUTH_APP_ID=your_app_id
WECHAT_OAUTH_APP_SECRET=your_app_secret
WEIBO_OAUTH_APP_ID=your_app_id
WEIBO_OAUTH_APP_SECRET=your_app_secret
```

### 6.2 手机号短信验证

**当前状态：** 开发/测试模式模拟运行。

**原因：** 短信验证码服务需要：
1. 注册企业主体
2. 签约短信服务商（阿里云短信/腾讯云短信等）
3. 完成短信模板审核

**Dev Mode 原理：**
- SMTP 配置留空时自动进入开发模式
- 发送验证码时，验证码直接打印在控制台并返回给前端（`dev_code` 字段）
- 前端 Toast 提示 `验证码：123456（开发模式）`
- 使用该 dev_code 即可完成注册、登录、重置密码等全部流程

### 6.3 本课程设计定位

> 以上功能限制属于**企业资质层面的合规要求**，非技术实现问题。
> 本课程设计项目以 **功能演示和技术验证** 为目的，所有功能在 dev mode 下可完整演示业务流程。
> 生产部署时需按上述说明补齐企业资质和第三方服务配置。

---

## 七、常见安装问题

### Q: 端口被占用？
```bash
# 查找占用进程
netstat -ano | findstr :8000
# 杀掉进程（替换 PID）
taskkill /F /PID 12345
```

### Q: `no such column` 错误？
数据库 schema 已更新但数据库文件是旧的。删除后重启自动重建：
```bash
Remove-Item -Force stock_fund_forum.db
```

### Q: `ModuleNotFoundError: No module named 'app'`？
确保 uvicorn 命令在 `backend/` 目录下执行：
```bash
cd backend
uvicorn app.main:app --port 8000 --reload
```

### Q: 前端页面白屏？
1. 确认前端 dev server 运行在 `http://localhost:5173`
2. 确认浏览器地址栏为 `http://localhost:5173/`（不是 `src/main.js`）
3. 检查控制台有无网络请求错误

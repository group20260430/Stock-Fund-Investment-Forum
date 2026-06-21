# 股票基金投资论坛

**课程名称：** 软件工程理论与实践课程设计  
**项目周期：** 2026年4月30日 ~ 2026年6月15日  

---

## 项目简介

面向股票、基金投资者的社区论坛系统，支持用户认证、板块分类、发帖互动、关注私信、内容审核等功能。  
本课程设计遵循软件工程五大阶段流程（需求→设计→实现→测试→交付），全程采用 AI（ChatGPT / Claude / Copilot）辅助提效。

---

## 小组成员

| 角色 | 班级 | 学号 | 姓名 | GitHub 用户名 |
|------|------|------|------|--------------|
| 项目负责人 | 软件2402班 | U202415227 | 贺嘉轩 | [kkk431](https://github.com/kkk431) |
| 后端开发 | 软件2402班 | U202410032 | 陶畅 | [AsimaBivcaks](https://github.com/AsimaBivcaks) |
| 后端开发/测试 | 软件2402班 | U202410003 | 张照炎 | [sshadow-sky](https://github.com/sshadow-sky) |
| 前端开发/文档 | 软件2402班 | U202411334 | 刘嘉成 | [Teamanmade](https://github.com/Teamanmade) |
| 前端开发 | 软件2402班 | U202410002 | 张桐尘 | [yigongwugezi](https://github.com/yigongwugezi) |
| 后端开发/运维 | 软件2402班 | U202415026 | 杨文弢 | [Luvef](https://github.com/Luvef) |

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 + Vite | Vue 3.x / Vite 6.x |
| UI 样式 | 手写 CSS (设计令牌) + Heroicons SVG | |
| 动画 | @vueuse/motion + @formkit/auto-animate | |
| 后端框架 | Python FastAPI | FastAPI 0.115+ |
| 数据库 (开发) | **SQLite** (零配置，文件即数据库) | 自动建表 |
| 数据库 (生产) | MySQL 8.0 + PyMySQL | 切换 .env 即可 |
| ORM | SQLAlchemy 2.0 | 声明式映射 |
| 认证方式 | JWT Token (bcrypt + PyJWT) | Access 2h / Refresh 7d |
| API 规范 | OpenAPI 3.0 | Swagger UI 自动生成 |
| 版本控制 | Git + GitHub | — |

---

## 项目结构

```text
Stock-Fund-Investment-Forum/
│
├── README.md                       # 项目总览（本文档）
├── frontend_core.md                # 前端核心开发日志
├── 团队分工与统一协作规范.md         # 团队分工与协作规范
├── user_stories.md                 # 用户故事（模块1）
├── use_cases.md                    # 交互场景（模块1）
├── architect.md                    # 架构与类设计（模块2）
├── backend_api.md                  # 后端接口文档（模块2）
├── ui_design.md                    # 前端UI设计（模块2）
├── ai.md                           # AI使用记录
├── assign.md                       # 工作完成情况
│
├── backend/                        # Python FastAPI 后端服务
│   ├── app/
│   │   ├── api/                    # API 路由层
│   │   │   ├── auth.py             # 用户认证（注册/登录/Token刷新）
│   │   │   ├── health.py           # 健康检查
│   │   │   ├── market.py           # 实时行情代理（东方财富）
│   │   │   └── posts.py            # 帖子相关接口
│   │   ├── core/                   # 核心配置
│   │   │   ├── config.py           # 配置(Pydantic Settings)
│   │   │   ├── security.py         # JWT/密码工具
│   │   │   └── dependencies.py     # 依赖注入（get_current_user等）
│   │   ├── db/                     # 数据库层
│   │   │   ├── base.py             # SQLAlchemy declarative_base
│   │   │   └── session.py          # 引擎 + 会话管理（SQLite/MySQL自适应）
│   │   ├── models/                 # ORM 数据模型
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── refresh_token.py    # JWT 刷新令牌
│   │   │   ├── certification.py    # 实名认证
│   │   │   └── risk_assessment.py  # 风险评估
│   │   ├── schemas/                # Pydantic 请求/响应 Schema
│   │   │   └── user.py
│   │   ├── services/               # 业务逻辑层
│   │   │   └── user_service.py
│   │   └── main.py                 # FastAPI 应用入口（含 lifespan 自动建表）
│   ├── .env                        # 环境变量（已配 SQLite + JWT密钥）
│   ├── .env.example                # 环境变量模板
│   ├── requirements.txt
│   ├── stock_fund_forum.db         # SQLite 数据库文件（自动生成，零配置）
│   └── README.md
│
├── frontend/                       # Vue 3 前端应用
│   ├── src/
│   │   ├── api/                    # API 调用封装（9个模块）
│   │   ├── components/             # 组件库
│   │   │   ├── common/             # 通用组件（NavBar/SideBar/Loading/
│   │   │   │                       #    Pagination/AppIcon/Toast/MarketCard等）
│   │   │   ├── layout/             # 布局组件（AppLayout）
│   │   │   ├── post/               # 帖子（PostCard/PostDetail/PostEditor）
│   │   │   ├── comment/            # 评论（CommentItem/CommentList）
│   │   │   └── user/               # 用户（UserCard/UserProfile）
│   │   ├── views/                  # 页面视图（17个，含admin子目录）
│   │   ├── stores/                 # Pinia 状态管理（auth/posts/user/toast）
│   │   ├── router/                 # Vue Router（21条路由 + 守卫）
│   │   ├── utils/                  # 工具（request/auth/format/icons）
│   │   ├── styles/                 # 全局样式（tokens/transitions/buttons）
│   │   ├── App.vue                 # 根组件（页面过渡动画）
│   │   └── main.js                 # 应用入口
│   ├── .env.example
│   ├── index.html
│   ├── vite.config.js              # Vite + unplugin-icons
│   └── package.json
│
└── database/                       # MySQL 建表脚本（生产环境手动建库用）
    ├── README.md
    ├── schema.sql
    └── seed.sql
```

---

## 文档索引

| 文档 | 阶段 | 说明 |
|------|------|------|
| `user_stories.md` | 模块1 - 需求分析 | 16条用户故事 + 验收标准 |
| `use_cases.md` | 模块1 - 需求分析 | 14个完整交互场景 |
| `architect.md` | 模块2 - 系统设计 | 架构图、类设计、技术选型 |
| `db.md` | 模块2 - 系统设计 | 数据库ER图、表结构说明 |
| `backend_api.md` | 模块2 - 系统设计 | OpenAPI 3.0 接口规范 |
| `ui_design.md` | 模块2 - 系统设计 | 前端页面设计 |
| `ai.md` | — | AI辅助使用记录 |
| `assign.md` | — | 成员工作完成情况 |

---

## 快速启动

### 0. 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.10+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| MySQL | 8.0+（可选） | 仅生产环境需要，开发环境使用 SQLite |

### 1. 启动后端（零配置，SQLite 自动建表）

```bash
cd backend

# 创建虚拟环境（仅首次）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 安装依赖（仅首次）
pip install -r requirements.txt

# 复制配置文件（仅首次，已默认使用 SQLite）
copy .env.example .env    # Windows
cp .env.example .env       # macOS / Linux

# 启动服务
uvicorn app.main:app --reload
```

> **SQLite 启动说明：**
> - 默认使用 **SQLite** 数据库（`stock_fund_forum.db`），零配置，启动即用
> - 首次启动时 FastAPI 会在 `lifespan` 中自动调用 `Base.metadata.create_all()` 创建所有表
> - 数据库文件位于 `backend/stock_fund_forum.db`，删除后重启即可重建
> - 如需切换到 MySQL，在 `.env` 中设置 `DATABASE_URL=mysql+pymysql://user:pass@host:3306/stock_fund_forum?charset=utf8mb4`

后端启动后访问：
- API 文档：http://localhost:8000/docs（Swagger UI 交互式文档）
- 健康检查：http://localhost:8000/api/health

### 2. 启动前端

```bash
cd frontend

# 安装依赖（仅首次）
npm install

# 启动开发服务器
npm run dev
```

前端默认地址：http://localhost:5173

### 3. 数据库切换（SQLite → MySQL）

如需使用 MySQL 替代 SQLite：

```bash
# 1. 先初始化 MySQL 数据库
cd database
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql

# 2. 修改 backend/.env
DATABASE_URL=mysql+pymysql://forum_user:forum_password@127.0.0.1:3306/stock_fund_forum?charset=utf8mb4

# 3. 重启后端即可
```

## 当前已完成

- ✅ 前端：17个页面、10个通用组件、7个业务组件、CSS设计令牌系统、Heroicons SVG图标、页面过渡动画、Toast通知、毛玻璃效果、实时行情数据（东方财富代理+迷你走势图）
- ✅ 后端：FastAPI 应用入口、CORS、用户注册/登录（JWT + bcrypt）、认证体系（基础/实名/专业）、风险评估问卷、内容审核队列、实时行情代理、SQLite 零配置自动建表
- ✅ 数据库：SQLAlchemy ORM 模型（User / RefreshToken / Certification / RiskAssessment），SQLite（开发）/ MySQL（生产）双模式
- ✅ API 文档：Swagger UI 自动生成（`/docs`），完整 RESTful 接口规范

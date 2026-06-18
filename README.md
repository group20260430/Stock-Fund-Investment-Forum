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
| 后端开发/测试 | 软件2402班 | U202410003 | 张桐尘 | [sshadow-sky](https://github.com/sshadow-sky) |
| 前端开发/文档 | 软件2402班 | U202411334 | 刘嘉成 | [Teamanmade](https://github.com/Teamanmade) |
| 前端开发 | 软件2402班 | U202410002 | 张照炎 | [yigongwugezi](https://github.com/yigongwugezi) |
| 后端开发/运维 | 软件2402班 | U202415026 | 杨文弢 | [Luvef](https://github.com/Luvef) |

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 + Vite | Vue 3.x / Vite 5.x |
| UI 样式 | Tailwind CSS | 最新 |
| 后端框架 | Python FastAPI | FastAPI 0.109+ |
| 数据库 | MySQL | 8.0+ |
| ORM | SQLAlchemy | 2.0+ |
| 认证方式 | JWT Token | PyJWT |
| API 规范 | OpenAPI 3.0 | Swagger UI 自动生成 |
| 版本控制 | Git + GitHub | — |

---

## 项目结构

```text
Stock-Fund-Investment-Forum/
│
├── README.md                       # 项目总览（本文档）
├── 团队分工与统一协作规范.md         # 团队分工与协作规范
├── user_stories.md                 # 用户故事（模块1）
├── use_cases.md                    # 交互场景（模块1）
├── architect.md                    # 架构与类设计（模块2）
├── db.md                           # 数据库设计（模块2）
├── backend_api.md                  # 后端接口文档（模块2）
├── ui_design.md                    # 前端UI设计（模块2）
├── ai.md                           # AI使用记录
├── assign.md                       # 工作完成情况
├── test.md                         # 测试报告（模块4）
├── install.md                      # 安装文档（模块5）
├── user_guid.md                    # 使用说明书（模块5）
│
├── backend/                        # Python 后端服务
│   ├── app/
│   │   ├── api/                    # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── health.py           # 健康检查
│   │   │   └── posts.py            # 帖子相关接口
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py           # 配置文件
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py          # 数据库会话
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI 应用入口
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                       # Vue 3 前端应用
│   ├── src/
│   │   ├── api/
│   │   │   └── posts.js            # 前端 API 请求封装
│   │   ├── components/
│   │   │   └── PostCard.vue        # 帖子卡片组件
│   │   ├── views/
│   │   │   └── ForumHome.vue       # 论坛首页视图
│   │   ├── App.vue                 # 应用根组件
│   │   ├── main.js                 # 应用入口
│   │   └── styles.css              # 全局样式
│   ├── .env.example
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── README.md
│
└── database/                       # MySQL 脚本
    ├── README.md
    ├── schema.sql                  # 建表脚本
    └── seed.sql                    # 初始数据
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

### 1. 初始化数据库

```bash
cd database
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

后端默认地址：http://localhost:8000

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：http://localhost:5173

## 当前已完成

- 创建 `backend/`、`frontend/`、`database/` 初始目录
- 后端提供 FastAPI 应用入口、CORS 配置、健康检查和帖子示例接口
- 前端提供 Vue 首页、帖子列表组件和 API 调用封装
- 数据库提供 MySQL 建库建表脚本和基础种子数据

## 下一步建议

- 接入真实用户注册、登录和 JWT 鉴权
- 使用 SQLAlchemy 模型替换后端示例数据
- 完善帖子、评论、点赞、收藏和关注接口
- 增加后台审核和板块管理功能

# 股票基金投资论坛

面向股票、基金投资者的社区论坛系统，计划支持用户认证、板块分类、发帖评论、关注关系、内容审核和投资主题讨论等功能。

## 项目简介
一个面向股票/基金投资者的社区论坛系统，支持用户认证、板块分类、发帖互动、关注私信、内容审核等功能。

## 小组成员
| 角色 | 班级 | 学号 | 姓名 | Gitee/GitHub用户名 |
|------|------|------|------|-------------------|
| 负责人 | 软件2402班 | U202415227 | 贺嘉轩 | https://github.com/kkk431 |
| 成员 | 软件2402班 | U202410032 | 陶畅 | https://github.com/AsimaBivcaks |
| 成员 | 软件2402班 | U202410003 | 张桐尘 | https://github.com/sshadow-sky |
| 成员 | 软件2402班 | U202411334 | 刘嘉成 | https://github.com/Teamanmade |
| 成员 | 软件2402班 | U202410002 | 张照炎 | https://github.com/yigongwugezi |
| 成员 | 软件2402班 | U202415026 | 杨文弢 | https://github.com/Luvef |


## 技术栈

- 前端：Vue3 + Vite
- 后端：Python + FastAPI
- 数据库：MySQL

## 项目结构

```text
.
├── backend/              # Python 后端服务
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置
│   │   ├── db/           # 数据库连接
│   │   └── models/       # 数据模型
│   ├── .env.example
│   └── requirements.txt
├── frontend/             # Vue 前端应用
│   ├── src/
│   │   ├── api/          # 前端接口请求
│   │   ├── components/   # 公共组件
│   │   └── views/        # 页面视图
│   ├── .env.example
│   └── package.json
└── database/             # MySQL 初始化脚本
    ├── schema.sql
    └── seed.sql
```

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

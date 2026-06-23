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
├── frontend_core.md                # 前端核心开发文档
├── frontend_pages.md               # 前端页面开发日志
│
├── backend/                        # Python 后端服务
│   ├── app/
│   │   ├── api/                    # API 路由层
│   │   │   ├── auth.py            # 用户认证
│   │   │   ├── posts.py           # 帖子相关
│   │   │   ├── community.py       # 社区/群组/消息
│   │   │   ├── discovery.py       # 发现/搜索
│   │   │   ├── interactions.py    # 点赞/收藏/评论
│   │   │   ├── market.py          # 市场数据
│   │   │   ├── admin.py           # 后台管理
│   │   │   ├── health.py          # 健康检查
│   │   │   └── ...                # 其他接口
│   │   ├── core/                   # 核心配置
│   │   ├── models/                 # 数据模型
│   │   ├── schemas/                # Pydantic 模式
│   │   ├── services/               # 业务服务层
│   │   └── main.py                 # FastAPI 应用入口
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                       # Vue 3 前端应用
│   ├── src/
│   │   ├── api/                    # API 请求封装
│   │   ├── components/             # 公共组件
│   │   ├── views/                  # 页面视图
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── router/                 # 路由配置
│   │   ├── utils/                  # 工具函数
│   │   ├── App.vue                 # 根组件
│   │   └── main.js                 # 入口
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── database/                       # MySQL 脚本
│   ├── schema.sql                  # 建表脚本
│   └── seed.sql                    # 初始数据
│
└── docs/                           # 文档与测试报告
    ├── backend_testing_guide.md
    ├── backend_smoke_test_zhangzhaoyan.md
    └── ...
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
| `frontend_core.md` | 模块3 - 实现 | 前端核心实现记录 |
| `frontend_pages.md` | 模块3 - 实现 | 前端页面开发日志 |
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
API 文档（Swagger UI）：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：http://localhost:5173

---

## 项目验证 / 冒烟测试

### 后端一键测试

进入后端目录后执行：

```powershell
cd backend
python run_backend_tests.py
```

当前后端一键测试覆盖主要接口测试和端到端测试，最新验证结果：

```text
RESULTS: 9 passed, 0 failed
```

也可以在项目根目录执行：

```powershell
python backend\run_backend_tests.py
```

### 前端构建验证

进入前端目录后执行：

```powershell
cd frontend
npm run build
```

当前前端生产构建已通过。构建过程中可能存在 Vite 非阻塞 warning，例如 chunk size 或动态导入提示，不影响 build 通过。

### 验证报告

详细验证记录见：

* `docs/backend_testing_guide.md`
* `docs/backend_quality_delivery_zhangzhaoyan.md`
* `docs/project_smoke_test_zhangzhaoyan.md`

注意：

* 以上验证不能替代完整人工 UI 测试、生产环境部署验证或真实数据库压测。
* 新增后端测试脚本后，应同步考虑加入 `backend/run_backend_tests.py`。

---

## 已实现功能

### 用户系统
- [x] 注册 / 登录（密码登录 + 验证码登录）
- [x] JWT 双 Token 认证（Access Token + Refresh Token）
- [x] 个人资料编辑与隐私设置
- [x] 积分与等级系统
- [x] 星标用户

### 内容系统
- [x] 帖子发布（富文本 + 话题标签 + 股票关联）
- [x] 帖子分类浏览
- [x] 评论、点赞、收藏、转发
- [x] 投票组件

### 社交系统
- [x] 关注 / 取关
- [x] 私信（一对一 + 群聊）
- [x] 未读消息计数与轮询
- [x] 用户搜索与推荐

### 社区
- [x] 群组创建与管理
- [x] 分组导航（市场讨论 / 主题专区 / 公司研究 / 问答求助）
- [x] 搜索（帖子 / 用户 / 股票 / 群组）

### 后台管理
- [x] 用户管理
- [x] 敏感词过滤
- [x] 内容审核
- [x] 操作日志

---

## 下一步建议

- 接入真实第三方登录（微信 / GitHub）
- 增加 WebSocket 实时消息推送
- 完善移动端适配
- 生产环境部署（Docker + Nginx）
- 性能优化与缓存策略

### 全项目一键验证

在项目根目录执行：

```powershell
python scripts\run_project_checks.py
```

该脚本会顺序运行后端一键测试和前端生产构建，并输出统一汇总结果。

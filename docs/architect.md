# 架构与类设计文档 (Architecture & Class Design)

> 项目：股票基金投资论坛
> 阶段：模块2 — AI辅助设计
> 迭代次数：3 轮

---

## 迭代记录

| 迭代 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-05-16 | 初始架构设计和技术选型 |
| V1.1 | 2026-05-18 | 细化类图，补充服务层和接口设计 |
| V1.2 | 2026-05-20 | 最终版本，补充安全设计和部署架构 |

---

## 1. 系统架构概览

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Vite)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 页面组件  │ │ 状态管理  │ │ 路由管理  │ │ API调用  │   │
│  │ (Views)  │ │ (Pinia)  │ │ (Router) │ │(Axios)  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/JSON (JWT Auth)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 后端 (FastAPI + Python)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  API路由  │ │ 服务层   │ │ 数据模型  │ │ 中间件   │   │
│  │ (Routers)│ │(Services)│ │(Models)  │ │(Auth)   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                        │                                 │
│              ┌─────────┴─────────┐                       │
│              │   SQLAlchemy ORM   │                       │
│              └─────────┬─────────┘                       │
└────────────────────────┬─────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │     MySQL 8.0       │
              │  (开发: SQLite)     │
              └─────────────────────┘
```

### 1.2 技术选型

| 层次 | 技术 | 版本 | 选型理由 |
|------|------|------|---------|
| **前端框架** | Vue 3 | 3.5+ | 组合式API，响应式系统，生态成熟 |
| **构建工具** | Vite | 6.0+ | 极速热更新，ESM原生支持 |
| **状态管理** | Pinia | 3.0+ | Vue 3官方推荐，TypeScript友好 |
| **路由** | Vue Router | 4.6+ | SPA路由，导航守卫 |
| **HTTP客户端** | Axios | 1.7+ | 拦截器支持Token刷新 |
| **UI组件** | Tiptap | 3.27+ | 富文本编辑器 |
| **图表** | ECharts + vue-echarts | 5.5+ | 行情K线图，统计图表 |
| **后端框架** | FastAPI | 0.109+ | 高性能异步，自动OpenAPI文档 |
| **ORM** | SQLAlchemy | 2.0+ | 成熟稳定，支持异步 |
| **数据库** | MySQL 8.0 / SQLite | - | MySQL生产，SQLite开发 |
| **认证** | JWT (PyJWT) | - | 无状态认证，Token Rotation |
| **密码学** | Passlib (bcrypt) | - | 密码哈希 |
| **数据验证** | Pydantic v2 | - | FastAPI原生支持 |
| **外部API** | httpx | - | 异步HTTP客户端（行情代理） |

---

## 2. V1.0 — 初始架构设计

### 2.1 前端架构

```
frontend/src/
├── api/              # API调用层
│   ├── auth.js       # 认证相关API
│   ├── posts.js      # 帖子相关API
│   ├── comments.js   # 评论相关API
│   ├── social.js     # 社交/发现API
│   ├── groups.js     # 群组API
│   ├── users.js      # 用户资料API
│   ├── notifications.js
│   ├── messages.js
│   ├── market.js     # 行情API
│   ├── search.js     # 搜索API
│   └── admin.js      # 管理后台API
├── components/       # 公共组件
│   ├── common/       # Loading, Pagination, EmptyState等
│   ├── post/         # PostCard, PostEditor, PollWidget等
│   ├── comment/      # CommentItem, CommentList
│   ├── user/         # UserCard, UserProfile
│   └── layout/       # AppLayout
├── router/           # 路由配置
│   └── index.js      # 路由表+导航守卫
├── stores/           # Pinia状态管理
│   ├── auth.js       # 认证状态
│   ├── toast.js      # Toast通知
│   └── settings.js   # 设置状态
├── styles/           # 全局样式
│   └── variables.css # CSS变量
├── utils/            # 工具函数
│   └── helpers.js    # 格式化/工具
└── views/            # 页面组件
    ├── Home.vue      # 首页
    ├── Login.vue     # 登录
    ├── Register.vue  # 注册
    ├── PostDetail.vue
    ├── UserProfile.vue
    ├── admin/        # 管理后台页面(12个)
    └── ...
```

### 2.2 后端架构

```
backend/app/
├── api/              # API路由层
│   ├── auth.py       # 认证接口
│   ├── posts.py      # 帖子接口
│   ├── interactions.py # 互动接口
│   ├── social_users.py # 社交接口
│   ├── community.py  # 群组/消息接口
│   ├── discovery.py  # 发现/搜索接口
│   ├── market.py     # 行情数据接口
│   ├── notifications.py # 通知接口
│   ├── admin.py      # 管理接口
│   ├── uploads.py    # 文件上传
│   └── health.py     # 健康检查
├── core/             # 核心配置
│   ├── config.py     # 配置管理
│   ├── security.py   # JWT/密码安全
│   └── dependencies.py # 依赖注入
├── models/           # ORM数据模型
│   ├── user.py       # 用户模型
│   ├── content.py    # 帖子/评论/点赞模型
│   ├── social.py     # 关注/星标模型
│   ├── community.py  # 群组/消息模型
│   ├── notification.py
│   ├── operations.py # 运营管理模型
│   ├── points.py     # 积分模型
│   ├── certification.py
│   ├── professional_certification.py
│   ├── risk_assessment.py
│   └── refresh_token.py
├── schemas/          # Pydantic校验模型
│   ├── user.py
│   ├── content.py
│   ├── social.py
│   ├── community.py
│   ├── interactions.py
│   ├── operations.py
│   └── privacy.py
├── services/         # 业务逻辑层
│   ├── user_service.py         # 用户业务
│   ├── points_service.py       # 积分系统
│   ├── activity_service.py     # 活动日志
│   ├── sensitive_word_service.py # 敏感词检测
│   ├── compliance_service.py   # 合规检测
│   ├── duplicate_content_service.py # 重复检测
│   ├── quality_service.py      # 内容质量评分
│   ├── mention_service.py      # @提及解析
│   └── email_service.py        # 邮件发送
├── db/               # 数据库配置
│   ├── base.py       # 声明基类
│   └── session.py    # 会话管理
└── config/           # 业务配置
    └── questions.py  # 风险评估题目
```

---

## 3. V1.1 — 类设计细化

### 3.1 核心实体类

#### User（用户）
```
┌──────────────────────────────────────┐
│                User                   │
├──────────────────────────────────────┤
│ - id: int                            │
│ - phone: str (unique)                │
│ - email: str (nullable, unique)      │
│ - password_hash: str                 │
│ - nickname: str                      │
│ - avatar_url: str (nullable)         │
│ - bio: str (nullable)                │
│ - role: enum(user/admin)             │
│ - status: enum(active/banned)        │
│ - auth_level: enum(basic/verified/   │
│       real_name/professional)        │
│ - risk_level: enum(conservative/     │
│       moderate/aggressive)           │
│ - points: int (default 0)            │
│ - level: int (default 1)             │
│ - tags: JSON (nullable)              │
│ - favorite_markets: JSON (nullable)  │
│ - risk_preference: str (nullable)    │
│ - privacy_settings: JSON             │
│ - register_type: enum(phone/email)   │
│ - created_at: datetime               │
│ - updated_at: datetime               │
├──────────────────────────────────────┤
│ + register() → User                  │
│ + login() → Token                    │
│ + update_profile() → User            │
│ + get_level(points) → int            │
│ + check_privacy(viewer) → dict       │
└──────────────────────────────────────┘
```

#### Post（帖子）
```
┌──────────────────────────────────────┐
│                Post                   │
├──────────────────────────────────────┤
│ - id: int                            │
│ - user_id: int (FK→users)            │
│ - category_id: int (FK→categories)   │
│ - title: str                         │
│ - content: text                      │
│ - post_type: enum(normal/longtext/   │
│       poll/realtime)                 │
│ - status: enum(published/review/     │
│       banned/draft)                  │
│ - is_essence: bool                   │
│ - is_live: bool                      │
│ - cover_image: str (nullable)        │
│ - tags: JSON                         │
│ - view_count: int                    │
│ - like_count: int                    │
│ - comment_count: int                 │
│ - collect_count: int                 │
│ - share_count: int                   │
│ - created_at: datetime               │
│ - updated_at: datetime               │
├──────────────────────────────────────┤
│ + create(user, data) → Post          │
│ + update(data) → Post                │
│ + delete() → bool                    │
│ + check_duplicate() → DuplicateResult│
│ + check_sensitive() → SensitiveResult│
│ + update_counts() → void             │
└──────────────────────────────────────┘
```

#### Comment（评论）
```
┌──────────────────────────────────────┐
│              Comment                  │
├──────────────────────────────────────┤
│ - id: int                            │
│ - post_id: int (FK→posts)            │
│ - user_id: int (FK→users)            │
│ - parent_id: int (nullable, FK→self) │
│ - reply_to_id: int (nullable)        │
│ - content: text                      │
│ - status: enum(published/review)     │
│ - like_count: int                    │
│ - created_at: datetime               │
├──────────────────────────────────────┤
│ + create(user, data) → Comment       │
│ + delete() → bool                    │
└──────────────────────────────────────┘
```

#### Group（群组）
```
┌──────────────────────────────────────┐
│               Group                   │
├──────────────────────────────────────┤
│ - id: int                            │
│ - owner_id: int (FK→users)           │
│ - name: str                          │
│ - description: text (nullable)       │
│ - avatar_url: str (nullable)         │
│ - is_public: bool                    │
│ - need_approval: bool                │
│ - member_count: int                  │
│ - created_at: datetime               │
│ - updated_at: datetime               │
├──────────────────────────────────────┤
│ + create(owner, data) → Group        │
│ + update(data) → Group               │
│ + disband() → bool                   │
│ + add_member(user) → GroupMember     │
│ + remove_member(user) → bool         │
└──────────────────────────────────────┘
```

### 3.2 服务层类

#### UserService
```
┌──────────────────────────────────────────────┐
│              UserService                       │
├──────────────────────────────────────────────┤
│ + register(db, data) → dict                  │
│ + login(db, data) → dict                     │
│ + send_code(db, data) → dict                 │
│ + verify_code(phone, code, type) → dict      │
│ + reset_password(db, data) → dict            │
│ + refresh_token(db, token_str) → dict        │
│ + get_profile(db, user_id) → UserProfile     │
│ + update_profile(db, user_id, data) → User   │
│ + submit_certification(db, user_id, data)     │
│ + submit_professional_cert(db, user_id, data) │
│ + submit_risk_assessment(db, user_id, data)   │
│ + get_privacy(db, user_id) → dict            │
│ + update_privacy(db, user_id, data) → dict    │
└──────────────────────────────────────────────┘
```

#### SensitiveWordService
```
┌──────────────────────────────────────────────┐
│          SensitiveWordService                  │
├──────────────────────────────────────────────┤
│ + check_content(db, text) → CheckResult      │
│ - _match_word(text, word) → bool              │
└──────────────────────────────────────────────┘
```

#### DuplicateContentService
```
┌──────────────────────────────────────────────┐
│        DuplicateContentService                 │
├──────────────────────────────────────────────┤
│ + check_duplicate_post(db, user_id, title,    │
│       content) → DuplicateResult              │
│ - _normalize_text(*texts) → str               │
└──────────────────────────────────────────────┘
```

#### PointsService
```
┌──────────────────────────────────────────────┐
│            PointsService                       │
├──────────────────────────────────────────────┤
│ + award_points(db, user_id, points, reason)   │
│ + get_level(points) → int                    │
└──────────────────────────────────────────────┘
```

### 3.3 三层架构关系

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   API路由层   │────▶│   服务层      │────▶│   数据模型    │
│  (FastAPI)   │     │  (Services)  │     │  (SQLAlchemy)│
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │
       │ HTTP请求/响应        │ 业务逻辑            │ ORM映射
       ▼                     ▼                     ▼
  请求体验证             事务管理              数据库操作
  (Pydantic Schema)     (DB Session)          (CRUD)
```

---

## 4. V1.2 — 最终设计补充

### 4.1 安全架构

```
┌─────────────────────────────────────────┐
│            安全架构设计                    │
├─────────────────────────────────────────┤
│                                         │
│  1. 认证机制                             │
│     ├─ JWT Access Token (2h)            │
│     ├─ Refresh Token Rotation (7d)      │
│     └─ Token 哈希存储 (SHA-256)          │
│                                         │
│  2. 密码安全                             │
│     ├─ bcrypt 密码哈希                   │
│     └─ 密码强度校验 (≥8位, 字母+数字)     │
│                                         │
│  3. 权限控制                             │
│     ├─ 基于角色的访问控制 (RBAC)          │
│     ├─ 资源所有者权限校验                 │
│     └─ 管理员权限隔离                    │
│                                         │
│  4. 数据安全                             │
│     ├─ 身份证号 AES 加密存储             │
│     ├─ 敏感信息脱敏                      │
│     └─ 隐私设置控制可见性                │
│                                         │
│  5. 接口安全                             │
│     ├─ CORS 跨域限制                     │
│     ├─ 文件上传类型白名单                 │
│     └─ 验证码防暴力破解                  │
└─────────────────────────────────────────┘
```

### 4.2 数据库ER图关系

```
users 1──N posts           users 1──N comments
users 1──N likes            users 1──N follows (follower)
users 1──N follows (following)  users 1──N notifications
users 1──N groups (owner)   users N──M groups (member)
users 1──N messages         users 1──N points_history
posts 1──N comments         posts 1──N likes
posts 1──N attachments      posts 1──N vote_options
posts 1──N favorites        posts 1──N shares
posts N──1 categories       posts N──M group_posts
comments 1──N comments (self-ref: parent_id)
```

### 4.3 部署架构

```
开发环境:
┌─────────────────────────────────────┐
│ 本地开发机                            │
│  ┌─────────┐  ┌─────────┐           │
│  │ Vite    │  │ Uvicorn │           │
│  │ :5173   │  │ :8000   │           │
│  └─────────┘  └────┬────┘           │
│                    │                 │
│              ┌─────▼─────┐          │
│              │  SQLite   │          │
│              └───────────┘          │
└─────────────────────────────────────┘

生产环境:
┌─────────────────────────────────────┐
│ 云服务器                              │
│  ┌──────────┐  ┌──────────┐         │
│  │ Nginx    │  │ Gunicorn │         │
│  │ 静态文件  │  │ Uvicorn  │         │
│  └──────────┘  └────┬─────┘         │
│                     │                │
│               ┌─────▼──────┐        │
│               │  MySQL 8.0 │        │
│               └────────────┘        │
└─────────────────────────────────────┘
```

### 4.4 API响应格式

```json
// 成功响应
{
  "code": 200,
  "message": "success",
  "data": { ... }
}

// 分页响应
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}

// 错误响应
{
  "detail": "错误信息描述"
}
```

---

## 5. 设计决策记录

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 前端框架 | React / Vue | Vue 3 | 组合式API更简洁，适合中小型项目 |
| 后端框架 | Django / FastAPI | FastAPI | 异步支持好，自动生成OpenAPI文档 |
| 数据库 | MySQL / PostgreSQL | MySQL 8.0 | 团队熟悉，utf8mb4支持中文 |
| ORM | SQLAlchemy / Tortoise | SQLAlchemy 2.0 | 成熟稳定，社区资源丰富 |
| 认证方式 | Session / JWT | JWT | 无状态，适合前后端分离 |
| 状态管理 | Vuex / Pinia | Pinia | Vue 3官方推荐，TypeScript友好 |
| 富文本编辑器 | Quill / Tiptap | Tiptap | 基于ProseMirror，扩展性强 |

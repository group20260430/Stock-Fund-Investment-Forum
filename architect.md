# 架构与类设计文档 (Architect & Class Design)

## 项目名称：股票基金投资论坛

**版本：** v1.0  
**最后更新：** 2026年6月18日  
**负责成员：** 贺嘉轩（架构师）

---

## 一、系统架构概览

### 1.1 总体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Vue 3 + Vite)                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ 用户系统 │ │ 内容系统  │ │ 社交系统  │ │ 搜索/管理后台 │  │
│  │ 页面    │ │ 页面     │ │ 页面     │ │ 页面          │  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬────────┘  │
│       └───────────┴────────────┴───────────────┘           │
│                        │ RESTful API (HTTP/JSON)            │
├────────────────────────┼────────────────────────────────────┤
│                  反向代理 / 负载均衡                          │
├────────────────────────┼────────────────────────────────────┤
│                    后端层 (FastAPI)                          │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ 用户模块 │ │ 内容模块  │ │ 社交模块  │ │ 管理运营模块   │  │
│  │ Service  │ │ Service  │ │ Service  │ │ Service       │  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬────────┘  │
│       └───────────┴────────────┴───────────────┘           │
│                        │ SQLAlchemy ORM                     │
├────────────────────────┼────────────────────────────────────┤
│                   数据库层 (MySQL 8.0)                       │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ 用户表   │ │ 内容表   │ │ 关系表    │ │ 审核/统计表    │  │
│  └─────────┘ └──────────┘ └──────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 分层架构说明

| 层 | 职责 | 技术选型 |
|----|------|---------|
| **表现层（前端）** | 用户交互、页面渲染、路由管理 | Vue 3 + Vite + Tailwind CSS |
| **API 网关层** | 统一入口、跨域处理、鉴权拦截 | FastAPI middleware |
| **业务逻辑层（后端）** | 业务规则处理、数据校验、事务管理 | FastAPI + SQLAlchemy |
| **数据访问层** | ORM 映射、数据库连接池管理 | SQLAlchemy 2.0 |
| **数据存储层** | 数据持久化、事务隔离、索引优化 | MySQL 8.0 |

### 1.3 前后端分离设计

```
前端 (Vue 3)                   后端 (FastAPI)               数据库 (MySQL)
    │                              │                           │
    │──── HTTP Request ──────────> │                           │
    │                              │── SQL Query ────────────> │
    │                              │<── Result Set ─────────── │
    │<── JSON Response ─────────── │                           │
    │                              │                           │
```

- 前端通过 `fetch` / `axios` 调用后端 RESTful API
- 后端返回统一格式的 JSON 响应
- 认证使用 JWT Token（Header: `Authorization: Bearer <token>`）
- 后端自动生成 OpenAPI 文档（`/docs` 端点）

---

## 二、技术选型说明

### 2.1 前端技术选型

| 技术 | 选型理由 |
|------|---------|
| **Vue 3** | 渐进式框架，学习成本低，组件化开发效率高 |
| **Vite** | 极速冷启动，HMR 热更新，开发体验优秀 |
| **Tailwind CSS** | 原子化 CSS，无需写大量自定义样式，响应式友好 |
| **Vue Router** | Vue 官方路由，SPA 页面管理 |
| **Pinia** | Vue 3 官方状态管理库，替代 Vuex |
| **Fetch API** | 原生 HTTP 请求，无需额外依赖 |

### 2.2 后端技术选型

| 技术 | 选型理由 |
|------|---------|
| **FastAPI** | 异步高性能，自动生成 OpenAPI 文档，类型校验 |
| **SQLAlchemy 2.0** | Python 最成熟的 ORM，支持异步，迁移方便 |
| **PyJWT** | 轻量级 JWT 生成与验证，适合无状态认证 |
| **PyMySQL** | MySQL 驱动，兼容性好 |
| **Pydantic** | 数据校验与序列化，与 FastAPI 深度集成 |

---

## 三、系统模块划分

```
stock_fund_forum
├── users                  # 用户系统模块
│   ├── auth               # 注册/登录/认证
│   ├── profile            # 个人资料管理
│   ├── certification      # 分级认证体系
│   └── assessment         # 风险评估问卷
├── content                # 内容系统模块
│   ├── categories         # 板块分类管理
│   ├── posts              # 帖子管理
│   ├── comments           # 评论管理
│   ├── votes              # 投票功能
│   ├── attachments        # 附件管理
│   └── interactions       # 点赞/收藏/转发
├── social                 # 社交与关系系统模块
│   ├── follows            # 关注/粉丝
│   ├── groups             # 群组管理
│   └── messages           # 私信系统
├── feed                   # 信息整合系统模块
│   ├── hot_topics         # 热榜排行
│   ├── search             # 全文搜索
│   └── recommendation     # 个性化推荐（选做）
└── admin                  # 管理运营系统模块
    ├── review             # 内容审核
    ├── user_management    # 用户管理
    └── statistics         # 数据统计
```

---

## 四、类设计

### 4.1 实体类图

```
┌─────────────────────────────────────────────────────────────────┐
│                          User                                    │
├─────────────────────────────────────────────────────────────────┤
│ - id: int                                                       │
│ - username: str                                                 │
│ - email: str                                                    │
│ - phone: str                                                    │
│ - password_hash: str                                            │
│ - avatar_url: str                                               │
│ - bio: str                                                      │
│ - role: UserRole (user/moderator/admin)                         │
│ - auth_level: AuthLevel (basic/verified/professional)           │
│ - risk_level: str                                               │
│ - status: UserStatus (active/disabled)                          │
│ - created_at: datetime                                          │
│ - updated_at: datetime                                          │
├─────────────────────────────────────────────────────────────────┤
│ + register()                                                    │
│ + login()                                                       │
│ + update_profile()                                              │
│ + submit_certification()                                        │
│ + complete_assessment()                                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ 1:N
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Post                                    │
├─────────────────────────────────────────────────────────────────┤
│ - id: int                                                       │
│ - user_id: int (FK)                                             │
│ - category_id: int (FK)                                         │
│ - post_type: PostType (normal/long/vote/discussion)             │
│ - title: str                                                    │
│ - content: text                                                 │
│ - view_count: int                                               │
│ - like_count: int                                               │
│ - comment_count: int                                            │
│ - status: PostStatus (draft/published/reviewing/rejected)       │
│ - last_activity_at: datetime                                    │
│ - created_at: datetime                                          │
│ - updated_at: datetime                                          │
├─────────────────────────────────────────────────────────────────┤
│ + create_post()                                                 │
│ + update_post()                                                 │
│ + delete_post()                                                 │
│ + get_detail()                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 核心类定义

```
┌────────────────────────────┐      ┌────────────────────────────┐
│        Category            │      │       Comment              │
├────────────────────────────┤      ├────────────────────────────┤
│ - id: int                  │      │ - id: int                  │
│ - name: str                │ 1:N  │ - post_id: int (FK)        │
│ - description: str         │◄─────│ - user_id: int (FK)        │
│ - sort_order: int          │      │ - parent_id: int (FK)      │
│ - is_active: bool          │      │ - content: text            │
│ - created_at: datetime     │      │ - status: CommentStatus    │
└────────────────────────────┘      │ - created_at: datetime    │
                                    │ - updated_at: datetime    │
┌────────────────────────────┐      └────────────────────────────┘
│     Follow                 │
├────────────────────────────┤
│ - follower_id: int (PK,FK) │      ┌────────────────────────────┐
│ - following_id: int (PK)   │      │       Vote                 │
│ - created_at: datetime     │      ├────────────────────────────┤
└────────────────────────────┘      │ - id: int                  │
                                    │ - post_id: int (FK)        │
┌────────────────────────────┐      │ - creator_id: int (FK)     │
│     Favorite               │      │ - question: str            │
├────────────────────────────┤      │ - vote_type: str           │
│ - id: int                  │      │ - deadline: datetime       │
│ - user_id: int (FK)        │      │ - status: VoteStatus       │
│ - post_id: int (FK)        │      └────────────────────────────┘
│ - folder_name: str         │
│ - created_at: datetime     │      ┌────────────────────────────┐
└────────────────────────────┘      │    VoteOption              │
                                    ├────────────────────────────┤
┌────────────────────────────┐      │ - id: int                  │
│     Group                   │      │ - vote_id: int (FK)        │
├────────────────────────────┤      │ - label: str               │
│ - id: int                  │      │ - count: int               │
│ - name: str                │      └────────────────────────────┘
│ - description: str         │
│ - type: GroupType          │      ┌────────────────────────────┐
│ - creator_id: int (FK)     │      │     Attachment             │
│ - created_at: datetime     │      ├────────────────────────────┤
└────────────────────────────┘      │ - id: int                  │
                                    │ - post_id: int (FK)        │
┌────────────────────────────┐      │ - file_name: str           │
│     GroupMember            │      │ - file_path: str           │
├────────────────────────────┤      │ - file_size: int           │
│ - id: int                  │      │ - file_type: str           │
│ - group_id: int (FK)       │      │ - is_approved: bool        │
│ - user_id: int (FK)        │      │ - created_at: datetime     │
│ - role: MemberRole         │      └────────────────────────────┘
│ - joined_at: datetime      │
└────────────────────────────┘
```

### 4.3 服务层类设计

```
┌──────────────────────────────────────┐
│          UserService                  │
├──────────────────────────────────────┤
│ + register(data: RegisterReq)        │
│ + login(data: LoginReq)              │
│ + send_verification_code(phone)      │
│ + verify_code(phone, code)           │
│ + get_profile(user_id)               │
│ + update_profile(user_id, data)      │
│ + submit_certification(user_id, ...) │
│ + complete_assessment(user_id, ...)  │
│ + get_user_by_id(user_id)            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│          PostService                  │
├──────────────────────────────────────┤
│ + create_post(user_id, data)         │
│ + get_post_detail(post_id)           │
│ + list_posts(category_id, page)      │
│ + update_post(post_id, data)         │
│ + delete_post(post_id)               │
│ + like_post(user_id, post_id)        │
│ + favorite_post(user_id, post_id)    │
│ + get_hot_posts(time_range)          │
│ + search_posts(keyword, filters)     │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        CommentService                 │
├──────────────────────────────────────┤
│ + create_comment(user_id, data)      │
│ + get_comments(post_id, page)        │
│ + reply_to_comment(user_id, data)    │
│ + delete_comment(comment_id)         │
│ + like_comment(user_id, comment_id)  │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        SocialService                  │
├──────────────────────────────────────┤
│ + follow_user(follower, following)   │
│ + unfollow_user(follower, following) │
│ + get_followers(user_id, page)       │
│ + get_following(user_id, page)       │
│ + get_feed(user_id, page)            │
│ + create_group(creator_id, data)     │
│ + join_group(user_id, group_id)      │
│ + send_message(sender, receiver, ...)│
│ + get_messages(user_id, page)        │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        AdminService                   │
├──────────────────────────────────────┤
│ + get_review_queue(page)             │
│ + approve_post(post_id, comment)     │
│ + reject_post(post_id, reason)       │
│ + get_user_list(filters, page)       │
│ + ban_user(user_id, reason, hours)   │
│ + get_statistics(time_range)         │
│ + export_report(format)              │
│ + handle_report(report_id, action)   │
└──────────────────────────────────────┘
```

### 4.4 API 路由层

```
┌──────────────────────────────────────┐
│          AuthRouter (APIRouter)       │
├──────────────────────────────────────┤
│ POST   /api/auth/register            │
│ POST   /api/auth/login               │
│ POST   /api/auth/send-code           │
│ POST   /api/auth/verify-code         │
│ POST   /api/auth/refresh-token       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│         UserRouter (APIRouter)        │
├──────────────────────────────────────┤
│ GET    /api/users/me                  │
│ PUT    /api/users/me                  │
│ GET    /api/users/{id}               │
│ POST   /api/users/certification      │
│ POST   /api/users/assessment         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│         PostRouter (APIRouter)        │
├──────────────────────────────────────┤
│ GET    /api/posts                    │
│ POST   /api/posts                    │
│ GET    /api/posts/{id}               │
│ PUT    /api/posts/{id}               │
│ DELETE /api/posts/{id}               │
│ POST   /api/posts/{id}/like          │
│ POST   /api/posts/{id}/favorite      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│      CommentRouter (APIRouter)        │
├──────────────────────────────────────┤
│ GET    /api/posts/{id}/comments      │
│ POST   /api/posts/{id}/comments      │
│ DELETE /api/comments/{id}            │
│ POST   /api/comments/{id}/like       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│      SocialRouter (APIRouter)         │
├──────────────────────────────────────┤
│ POST   /api/users/{id}/follow        │
│ DELETE /api/users/{id}/follow        │
│ GET    /api/me/followers              │
│ GET    /api/me/following              │
│ GET    /api/me/feed                   │
│ POST   /api/groups                   │
│ GET    /api/groups                   │
│ POST   /api/groups/{id}/join         │
│ GET    /api/messages                 │
│ POST   /api/messages                 │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│       AdminRouter (APIRouter)         │
├──────────────────────────────────────┤
│ GET    /api/admin/review-queue       │
│ POST   /api/admin/review/{id}/approve│
│ POST   /api/admin/review/{id}/reject │
│ GET    /api/admin/users              │
│ POST   /api/admin/users/{id}/ban     │
│ GET    /api/admin/statistics         │
│ GET    /api/admin/reports            │
│ POST   /api/admin/reports/{id}       │
└──────────────────────────────────────┘
```

---

## 五、目录结构规范

### 5.1 后端目录

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证接口
│   │   ├── users.py         # 用户接口
│   │   ├── posts.py         # 帖子接口
│   │   ├── comments.py      # 评论接口
│   │   ├── categories.py    # 板块接口
│   │   ├── social.py        # 社交接口
│   │   ├── groups.py        # 群组接口
│   │   ├── messages.py      # 私信接口
│   │   ├── search.py        # 搜索接口
│   │   └── admin.py         # 管理接口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置
│   │   ├── security.py      # JWT/密码工具
│   │   └── dependencies.py  # 依赖注入
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py       # 数据库会话
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # 用户模型
│   │   ├── post.py          # 帖子模型
│   │   ├── comment.py       # 评论模型
│   │   ├── category.py      # 板块模型
│   │   ├── follow.py        # 关注模型
│   │   ├── favorite.py      # 收藏模型
│   │   ├── vote.py          # 投票模型
│   │   ├── group.py         # 群组模型
│   │   ├── message.py       # 私信模型
│   │   └── attachment.py    # 附件模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py          # 用户Pydantic schema
│   │   ├── post.py          # 帖子schema
│   │   └── common.py        # 通用schema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   ├── social_service.py
│   │   └── admin_service.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_posts.py
│   └── test_comments.py
├── .env.example
├── requirements.txt
└── README.md
```

### 5.2 前端目录

```
frontend/
├── src/
│   ├── api/
│   │   ├── auth.js
│   │   ├── posts.js
│   │   ├── comments.js
│   │   ├── users.js
│   │   ├── social.js
│   │   ├── groups.js
│   │   ├── search.js
│   │   └── admin.js
│   ├── components/
│   │   ├── common/
│   │   │   ├── NavBar.vue
│   │   │   ├── SideBar.vue
│   │   │   ├── Loading.vue
│   │   │   └── Pagination.vue
│   │   ├── post/
│   │   │   ├── PostCard.vue
│   │   │   ├── PostDetail.vue
│   │   │   └── PostEditor.vue
│   │   ├── comment/
│   │   │   ├── CommentList.vue
│   │   │   └── CommentItem.vue
│   │   └── user/
│   │       ├── UserCard.vue
│   │       └── UserProfile.vue
│   ├── views/
│   │   ├── Home.vue
│   │   ├── Login.vue
│   │   ├── Register.vue
│   │   ├── PostDetail.vue
│   │   ├── CreatePost.vue
│   │   ├── UserProfile.vue
│   │   ├── Search.vue
│   │   ├── Category.vue
│   │   ├── GroupList.vue
│   │   ├── GroupDetail.vue
│   │   ├── Messages.vue
│   │   └── admin/
│   │       ├── Dashboard.vue
│   │       ├── ReviewQueue.vue
│   │       └── UserManagement.vue
│   ├── stores/
│   │   ├── auth.js
│   │   ├── posts.js
│   │   └── user.js
│   ├── router/
│   │   └── index.js
│   ├── utils/
│   │   ├── request.js       # HTTP 请求封装
│   │   └── auth.js          # Token 管理
│   ├── App.vue
│   ├── main.js
│   └── styles.css
├── .env.example
├── index.html
├── vite.config.js
├── package.json
└── README.md
```

---

## 六、数据流与请求流程

### 6.1 认证流程

```
Client                          Server
  │                               │
  │── POST /api/auth/register ──> │  [注册]
  │                               │── 校验输入
  │                               │── 写入数据库
  │<── { user, token } ──────── │
  │                               │
  │── POST /api/auth/login ────> │  [登录]
  │                               │── 验证密码
  │                               │── 生成 JWT
  │<── { user, token } ──────── │
  │                               │
  │── GET /api/users/me ───────> │  [鉴权请求]
  │   Authorization: Bearer jwt  │── 验证 Token
  │                               │── 返回用户信息
  │<── { user } ─────────────── │
```

### 6.2 发帖审核流程

```
                  ┌──────────┐
                  │ 用户提交  │
                  │   帖子    │
                  └────┬─────┘
                       │
                       ▼
                ┌──────────────┐
                │  自动审核     │
                │  (敏感词+)    │
                └──────┬───────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
     ┌────────────┐        ┌──────────────┐
     │  通过       │        │  可疑/违规    │
     └──────┬─────┘        └──────┬───────┘
            │                     │
            ▼                     ▼
     ┌────────────┐        ┌──────────────┐
     │  直接发布   │        │ 进入人工审核  │
     └────────────┘        └──────┬───────┘
                                  │
                       ┌──────────┴──────────┐
                       ▼                     ▼
                ┌──────────────┐     ┌──────────────┐
                │  审核通过     │     │  审核拒绝     │
                │   → 发布      │     │   → 通知作者  │
                └──────────────┘     └──────────────┘
```

---

## 七、错误处理规范

### 7.1 统一响应格式

**成功响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**分页响应：**
```json
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
```

**错误响应：**
```json
{
  "code": 400,
  "message": "参数错误",
  "errors": {
    "phone": "手机号格式不正确",
    "password": "密码长度至少8位"
  }
}
```

### 7.2 HTTP 状态码使用

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 | OK | 请求成功 |
| 201 | Created | 创建资源成功 |
| 400 | Bad Request | 参数校验失败 |
| 401 | Unauthorized | 未登录或 Token 过期 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如重复注册） |
| 422 | Unprocessable | 数据格式错误 |
| 429 | Too Many Requests | 频率限制 |
| 500 | Internal Error | 服务器内部错误 |

---

## 八、安全设计

### 8.1 认证与授权

- 密码使用 `bcrypt` 哈希存储
- JWT Token 有效期：Access Token 2小时，Refresh Token 7天
- 敏感接口需要二次验证（如修改密码、实名认证）
- 不同角色权限分级：普通用户 → 认证用户 → 版主 → 管理员

### 8.2 数据安全

- 所有密码、Token 不在日志中输出
- 用户隐私字段（电话、身份证号）加密存储
- 文件上传限制类型和大小（PDF/Excel ≤ 10MB）
- 前后端均做输入校验（前端用户体验 + 后端安全防线）

### 8.3 防攻击措施

- 接口频率限制（Rate Limiting）：注册/登录 5次/分钟
- SQL 注入防护：使用 SQLAlchemy ORM 参数化查询
- XSS 防护：前端渲染时转义 HTML 标签
- CORS 配置：仅允许前端域名访问

---

*本文档由贺嘉轩编写，经团队讨论确认。后续迭代需保持文档与代码同步更新。*

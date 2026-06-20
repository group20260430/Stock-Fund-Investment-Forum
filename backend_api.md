# 后端接口文档 (Backend API)

## 项目名称：股票基金投资论坛

**API 规范：** RESTful + OpenAPI 3.0  
**基础 URL：** `http://localhost:8000/api`  
**版本：** v1.0  
**更新日期：** 2026年6月18日  

---

## 一、接口设计总规范

### 1.1 通用规则

| 项目 | 规范 |
|------|------|
| **请求方式** | GET（查询）、POST（创建）、PUT（全量更新）、PATCH（部分更新）、DELETE（删除） |
| **URL 风格** | 名词复数，如 `/users`、`/posts/{id}` |
| **请求体格式** | `application/json` |
| **响应格式** | `application/json`，统一包裹 |
| **认证方式** | JWT Bearer Token（`Authorization: Bearer <token>`） |
| **分页** | `?page=1&size=20`，返回 `{ items: [...], total: N, page: N, size: N }` |
| **排序** | `?sort=created_at&order=desc` |
| **筛选** | `?field=value`，多字段间为 AND 关系 |
| **搜索** | `?keyword=xxx` |

### 1.2 统一响应格式

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
    "size": 20
  }
}
```

**错误响应：**
```json
{
  "code": 400,
  "message": "具体错误描述",
  "data": null
}
```

### 1.3 HTTP 状态码约定

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 创建成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 参数错误或业务校验失败 |
| 401 | Unauthorized | 未认证或 Token 过期 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如重复注册） |
| 422 | Unprocessable Entity | 请求体校验失败 |
| 429 | Too Many Requests | 接口限流 |
| 500 | Internal Server Error | 服务器内部错误 |

### 1.4 错误码约定

| 错误码范围 | 所属模块 |
|-----------|---------|
| 1001~1099 | 用户系统 |
| 2001~2099 | 内容系统 |
| 3001~3099 | 社交系统 |
| 4001~4099 | 搜索/聚合 |
| 5001~5099 | 管理运营 |

### 1.5 常用请求头

```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
Accept: application/json
```

---

## 二、模块1：用户系统 API

### 2.1 注册与认证

---

#### POST /auth/register — 用户注册

**请求体：**
```json
{
  "phone": "13800138000",
  "password": "Abc@123456",
  "nickname": "小明",
  "avatar_url": "https://example.com/avatar.png",
  "register_type": "phone"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | string | Y | 手机号，11位数字 |
| `password` | string | Y | 密码，8~32位，含字母+数字 |
| `nickname` | string | N | 昵称，2~20字符 |
| `avatar_url` | string | N | 头像URL |
| `register_type` | string | N | 注册方式：`phone` / `email` / `wechat` / `weibo` |

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "user_id": 1,
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**错误示例 (409)：**
```json
{
  "code": 409,
  "message": "该手机号已注册",
  "data": null
}
```

---

#### POST /auth/send-code — 发送验证码

**请求体：**
```json
{
  "phone": "13800138000",
  "type": "register"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | string | Y | 手机号 |
| `type` | string | Y | 验证码类型：`register` / `login` / `reset_password` |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "验证码已发送",
  "data": {
    "expire_in": 300
  }
}
```

---

#### POST /auth/login — 用户登录

**请求体：**
```json
{
  "phone": "13800138000",
  "password": "Abc@123456",
  "login_type": "password"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | string | Y | 手机号或邮箱 |
| `password` | string | Y | 密码（密码登录时） |
| `code` | string | N | 验证码（验证码登录时） |
| `login_type` | string | Y | 登录方式：`password` / `code` |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user_id": 1,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "nickname": "小明",
      "avatar_url": "...",
      "role": "user",
      "auth_level": "basic"
    }
  }
}
```

---

#### POST /auth/refresh — 刷新 Token

**请求头：** `Authorization: Bearer <token>`  
**请求体：** 无

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "Token 已刷新",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 86400
  }
}
```

---

### 2.2 认证管理

---

#### GET /auth/me — 获取当前用户信息

**请求头：** `Authorization: Bearer <token>`

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "nickname": "小明",
    "avatar_url": "https://...",
    "bio": "价值投资者，专注消费行业",
    "phone": "138****8000",
    "email": "xiao@example.com",
    "role": "user",
    "auth_level": "basic",
    "is_professional": false,
    "risk_level": "moderate",
    "investment_tags": ["价值投资", "消费", "A股"],
    "follow_markets": ["A股", "港股"],
    "achievements": {
      "posts_count": 15,
      "elite_posts": 2,
      "influence_score": 320,
      "badges": ["新手入门", "精华作者"]
    },
    "created_at": "2026-05-01T10:00:00Z"
  }
}
```

---

#### PUT /auth/profile — 更新个人资料

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "nickname": "投资达人小明",
  "bio": "资深价值投资者",
  "avatar_url": "https://...new-avatar.png",
  "investment_tags": ["价值投资", "消费", "科技"],
  "follow_markets": ["A股", "港股", "美股"],
  "risk_preference": "aggressive"
}
```

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": { ... }
}
```

---

#### POST /auth/certification — 申请实名认证

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "id_card_front": "data:image/png;base64,...",
  "id_card_back": "data:image/png;base64,...",
  "real_name": "张某",
  "id_number": "110101199001011234"
}
```

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "认证申请已提交，等待审核",
  "data": {
    "status": "pending"
  }
}
```

---

#### POST /auth/risk-assessment — 提交风险评估问卷

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "answers": [
    {"question_id": 1, "answer": "A"},
    {"question_id": 2, "answer": "C"}
  ],
  "total_questions": 15
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `answers` | array | Y | 答案列表，每项包含 `question_id` (int) 和 `answer` (string, A~E) |
| `total_questions` | int | N | 题目总数，不传则从 answers 数组长度推断 |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "评估完成",
  "data": {
    "assessment_id": 1,
    "risk_level": "moderate",
    "score": 65,
    "max_score": 100,
    "suggestion": "您属于中等风险承受型投资者..."
  }
}
```

**错误示例 (400)：**
```json
{
  "code": 400,
  "message": "{\"code\": 1001, \"message\": \"题目 1 的答案 'X' 无效，只能为 A/B/C/D/E\"}",
  "data": null
}
```

| 错误码 | 说明 |
|--------|------|
| 1001 | 答案格式无效（不在 A~E 范围内） |
| 1002 | 问卷不完整（答案数量与 total_questions 不一致） |

---

#### GET /auth/risk-assessment/questions — 获取风险评估问卷

**请求头：** `Authorization: Bearer <token>`

**请求体：** 无

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "question_id": 1,
      "question_text": "您的年龄范围是？",
      "choices": [
        {"label": "A", "text": "60岁以上", "score": 1},
        {"label": "B", "text": "51-60岁", "score": 2},
        {"label": "C", "text": "41-50岁", "score": 3},
        {"label": "D", "text": "31-40岁", "score": 4},
        {"label": "E", "text": "30岁以下", "score": 5}
      ]
    }
  ]
}
```

**说明：** 问卷共 15 道题，覆盖财务状况、投资经验、风险态度和行为模式四个维度。每题 5 个选项（A~E），分值 1~5。

---

#### GET /auth/risk-assessment/history — 获取历史评估记录

**请求头：** `Authorization: Bearer <token>`

**查询参数：** `?page=1&size=20`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码，≥1 |
| `size` | int | 20 | 每页数量，1~50 |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "score": 65,
        "risk_level": "moderate",
        "total_questions": 15,
        "created_at": "2026-06-20T10:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

**说明：** 按评估时间倒序排列，支持多次评估历史追溯。

## 三、模块2：内容系统 API

### 3.1 板块分类

---

#### GET /categories — 获取板块列表

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "综合讨论",
      "description": "综合投资讨论区",
      "sort_order": 1,
      "post_count": 1200
    },
    {
      "id": 2,
      "name": "股票市场",
      "description": "A股、港股、美股讨论",
      "sort_order": 2,
      "post_count": 890
    },
    {
      "id": 3,
      "name": "基金投资",
      "description": "基金配置与策略",
      "sort_order": 3,
      "post_count": 650
    },
    {
      "id": 4,
      "name": "问答求助",
      "description": "新手提问与投资解惑",
      "sort_order": 4,
      "post_count": 430
    },
    {
      "id": 5,
      "name": "投资策略",
      "description": "价值投资、量化投资等",
      "sort_order": 5,
      "post_count": 310
    }
  ]
}
```

---

### 3.2 帖子管理

---

#### GET /posts — 获取帖子列表

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `category_id` | int | N | 板块ID筛选 |
| `sort` | string | N | 排序方式：`latest` / `hot` / `elite` |
| `page` | int | N | 页码，默认1 |
| `size` | int | N | 每页条数，默认20，最大50 |
| `keyword` | string | N | 关键词搜索 |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "A股市场今日讨论",
        "content_summary": "今天大盘走势回顾...",
        "author": {
          "id": 1,
          "nickname": "小明",
          "avatar_url": "...",
          "auth_level": "basic"
        },
        "category": {
          "id": 1,
          "name": "综合讨论"
        },
        "post_type": "normal",
        "view_count": 256,
        "like_count": 12,
        "comment_count": 3,
        "is_elite": false,
        "tags": ["A股", "盘面分析"],
        "created_at": "2026-06-01T10:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

---

#### GET /posts/{id} — 获取帖子详情

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "A股市场今日讨论",
    "content": "今天大盘走势回顾...（完整内容）",
    "post_type": "long_article",
    "author": {
      "id": 1,
      "nickname": "小明",
      "avatar_url": "...",
      "auth_level": "basic",
      "is_followed": true
    },
    "category": {
      "id": 1,
      "name": "综合讨论"
    },
    "attachments": [
      {"file_name": "分析报告.pdf", "file_url": "...", "file_size": 2048000}
    ],
    "view_count": 256,
    "like_count": 12,
    "comment_count": 3,
    "collect_count": 5,
    "share_count": 2,
    "is_liked": false,
    "is_collected": true,
    "tags": ["A股", "盘面分析"],
    "created_at": "2026-06-01T10:00:00Z",
    "updated_at": "2026-06-01T15:00:00Z"
  }
}
```

---

#### POST /posts — 创建帖子

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "category_id": 1,
  "title": "A股市场今日讨论",
  "content": "今天大盘走势回顾...（完整内容）",
  "post_type": "long_article",
  "tags": ["A股", "盘面分析"],
  "attachments": [
    {"file_name": "分析报告.pdf", "file_url": "..."}
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `category_id` | int | Y | 板块ID |
| `title` | string | Y | 标题，1~120字符 |
| `content` | string | Y | 内容，支持HTML/Markdown |
| `post_type` | string | Y | 类型：`normal` / `long_article` / `poll` / `moment` |
| `tags` | string[] | N | 标签列表 |
| `attachments` | object[] | N | 附件列表 |

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "发布成功",
  "data": {
    "id": 1,
    "status": "published"
  }
}
```

---

#### PUT /posts/{id} — 编辑帖子

**请求头：** `Authorization: Bearer <token>`（仅作者和管理员）

**请求体：** 同创建帖子

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "编辑成功",
  "data": { "id": 1 }
}
```

---

#### DELETE /posts/{id} — 删除帖子

**请求头：** `Authorization: Bearer <token>`（仅作者和管理员）

**成功响应 (204)：** 无内容

---

### 3.3 投票功能

---

#### POST /posts/{id}/vote — 参与投票

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "option_ids": [1]
}
```

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "投票成功",
  "data": {
    "results": [
      {"option_id": 1, "option_text": "看好", "votes": 42, "percentage": 42.0},
      {"option_id": 2, "option_text": "持平", "votes": 33, "percentage": 33.0},
      {"option_id": 3, "option_text": "看空", "votes": 25, "percentage": 25.0}
    ]
  }
}
```

---

### 3.4 评论系统

---

#### GET /posts/{id}/comments — 获取评论列表

**查询参数：** `?page=1&size=20`

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "content": "分析得很好！",
        "author": {
          "id": 2,
          "nickname": "投资达人",
          "avatar_url": "..."
        },
        "like_count": 5,
        "is_liked": false,
        "replies": [
          {
            "id": 10,
            "content": "同意你的观点",
            "author": {"id": 1, "nickname": "小明", "avatar_url": "..."},
            "reply_to": {"id": 2, "nickname": "投资达人"},
            "created_at": "2026-06-01T12:00:00Z"
          }
        ],
        "reply_count": 1,
        "created_at": "2026-06-01T11:00:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "size": 20
  }
}
```

---

#### POST /posts/{id}/comments — 发表评论

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "content": "分析得很好！",
  "parent_id": null,
  "reply_to_id": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | Y | 评论内容，最多2000字 |
| `parent_id` | int | N | 父评论ID，一级评论为null |
| `reply_to_id` | int | N | 回复的目标用户评论ID |

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "评论成功",
  "data": {
    "id": 1,
    "content": "分析得很好！",
    "created_at": "2026-06-01T11:00:00Z"
  }
}
```

---

### 3.5 点赞 / 收藏 / 转发

---

#### POST /posts/{id}/like — 点赞/取消点赞

**请求头：** `Authorization: Bearer <token>`  
**请求体：** 无（切换点赞状态）

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_liked": true,
    "like_count": 13
  }
}
```

---

#### POST /posts/{id}/collect — 收藏/取消收藏

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "folder_name": "基金分析"
}
```

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_collected": true,
    "collect_count": 6,
    "folder_name": "基金分析"
  }
}
```

---

#### GET /users/me/collections — 获取收藏列表

**请求头：** `Authorization: Bearer <token>`  
**查询参数：** `?folder=基金分析&page=1&size=20`

---

#### POST /posts/{id}/share — 转发帖子

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "share_type": "timeline",
  "comment": "值得一读"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `share_type` | string | Y | 转发类型：`timeline` / `message` / `group` |
| `comment` | string | N | 转发附言 |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "转发成功",
  "data": { ... }
}
```

---

## 四、模块3：社交与关系系统 API

### 4.1 关注与粉丝

---

#### POST /users/{id}/follow — 关注/取消关注用户

**请求头：** `Authorization: Bearer <token>`  
**请求体：** 无（切换关注状态）

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_followed": true,
    "followers_count": 100,
    "following_count": 50
  }
}
```

---

#### GET /users/{id}/followers — 获取粉丝列表

**查询参数：** `?page=1&size=20`

**成功响应 (200)：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 2,
        "nickname": "投资达人",
        "avatar_url": "...",
        "auth_level": "professional",
        "is_followed": true
      }
    ],
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

---

#### GET /users/{id}/following — 获取关注列表

---

#### PUT /users/me/starred — 设置星标用户

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "user_id": 2,
  "is_starred": true
}
```

---

### 4.2 群组功能

---

#### POST /groups — 创建群组

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "name": "5G概念股深度讨论组",
  "description": "专注于5G产业链上市公司分析",
  "avatar_url": "https://...",
  "visibility": "public",
  "need_approval": true,
  "invite_ids": [2, 3]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `visibility` | string | Y | `public` / `private` |
| `need_approval` | bool | N | 加入是否需要审核 |

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "群组创建成功",
  "data": {
    "id": 1,
    "name": "5G概念股深度讨论组",
    "member_count": 3,
    "role": "owner"
  }
}
```

---

#### GET /groups — 获取群组列表

**查询参数：** `?type=my&page=1&size=20`（`type`= `my` / `explore` / `joined`）

---

#### POST /groups/{id}/join — 申请/加入群组

**请求头：** `Authorization: Bearer <token>`

---

#### POST /groups/{id}/members/{user_id}/approve — 审核成员（管理员）

---

#### POST /groups/{id}/posts — 在群组内发帖

---

## 五、模块4：信息整合系统 API

### 5.1 个性化 Feed

---

#### GET /feed — 获取个性化内容流

**请求头：** `Authorization: Bearer <token>`  
**查询参数：** `?page=1&size=20`

**成功响应 (200)：** 同帖子列表，但按个性化算法排序

---

### 5.2 热榜

---

#### GET /hot — 获取热榜

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `period` | string | N | 时间范围：`daily` / `weekly` / `monthly` |
| `market` | string | N | 市场分类：`all` / `a_stock` / `hk_stock` / `fund` |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "rank": 1,
      "topic": "比亚迪",
      "heat_score": 9850,
      "discussion_count": 256,
      "market": "A股",
      "change_indicator": "+3.2%",
      "trending_posts": [
        {"id": 1, "title": "比亚迪Q2业绩前瞻", "author": "..."}
      ]
    }
  ]
}
```

---

### 5.3 搜索

---

#### GET /search — 全文搜索

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | Y | 搜索关键词 |
| `type` | string | N | 搜索类型：`all` / `post` / `user` / `stock` |
| `category_id` | int | N | 板块筛选 |
| `time_range` | string | N | 时间：`all` / `day` / `week` / `month` |
| `sort` | string | N | 排序：`relevance` / `time` / `heat` |
| `is_elite` | bool | N | 仅看精华帖 |
| `market` | string | N | 市场分类 |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "size": 20,
    "items": [
      {
        "type": "post",
        "id": 1,
        "title": "比亚迪投资分析",
        "content_summary": "...中提到的比亚迪...",
        "author": {"id": 1, "nickname": "小明"},
        "heat": 120,
        "created_at": "2026-06-01T10:00:00Z"
      }
    ]
  }
}
```

---

#### GET /search/suggestions — 搜索联想

**查询参数：** `?keyword=比亚迪&type=all`

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "stocks": [
      {"code": "002594", "name": "比亚迪", "market": "SZ"}
    ],
    "users": [
      {"id": 1, "nickname": "比亚迪分析师"}
    ],
    "topics": [
      "比亚迪投资分析",
      "比亚迪Q2业绩"
    ]
  }
}
```

---

### 5.4 私信系统

---

#### GET /messages — 获取私信列表（按会话分组）

**请求头：** `Authorization: Bearer <token>`

---

#### POST /messages — 发送私信

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "receiver_id": 2,
  "content": "你好，关于你的分析贴想请教一下",
  "message_type": "text",
  "attachment_url": null
}
```

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "发送成功",
  "data": {
    "id": 1,
    "created_at": "2026-06-01T10:00:00Z"
  }
}
```

---

## 六、模块5：管理运营系统 API

### 6.1 内容审核

---

#### GET /admin/review-queue — 获取审核队列

**请求头：** `Authorization: Bearer <token>`（管理员）  
**查询参数：** `?page=1&size=20&status=pending`

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "content_type": "post",
        "title": "某股票推荐分析",
        "author": {"id": 1, "nickname": "小明"},
        "flags": ["敏感词:推荐股票"],
        "status": "pending",
        "submitted_at": "2026-06-01T10:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "size": 20
  }
}
```

---

#### POST /admin/review-queue/{id}/review — 审核操作

**请求头：** `Authorization: Bearer <token>`（管理员）

**请求体：**
```json
{
  "action": "approve",
  "comment": "内容合规，通过审核"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | Y | `approve` / `reject` / `edit` |
| `comment` | string | N | 审核意见（拒绝时必填） |

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "审核完成",
  "data": {
    "status": "approved"
  }
}
```

---

### 6.2 举报管理

---

#### POST /report — 提交举报

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "target_id": 1,
  "target_type": "post",
  "reason": "illegal_stock_promotion",
  "description": "该帖涉及违规荐股"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | Y | `fake_info` / `personal_attack` / `illegal_stock_promotion` / `spam` / `other` |

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "举报成功，感谢您的反馈",
  "data": null
}
```

---

### 6.3 用户管理

---

#### GET /admin/users — 获取用户列表（管理员）

**查询参数：** `?page=1&size=20&status=active&keyword=xxx`

---

#### POST /admin/users/{id}/ban — 封禁/解封用户

**请求头：** `Authorization: Bearer <token>`（管理员）

**请求体：**
```json
{
  "action": "ban",
  "reason": "多次发布违规内容",
  "duration_hours": 72
}
```

---

### 6.4 数据统计

---

#### GET /admin/stats/overview — 获取总览统计数据

**请求头：** `Authorization: Bearer <token>`（管理员）

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "daily_active_users": 1250,
    "new_users_today": 35,
    "total_posts": 12000,
    "total_comments": 45000,
    "pending_review": 8,
    "reports_today": 5
  }
}
```

---

#### GET /admin/stats/trend — 获取趋势数据

**查询参数：** `?period=weekly&start_date=2026-05-01&end_date=2026-06-01`

**成功响应 (200)：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_activity": [
      {"date": "2026-05-01", "dau": 1000, "new_users": 20},
      {"date": "2026-05-02", "dau": 1100, "new_users": 25}
    ],
    "content_stats": [
      {"date": "2026-05-01", "posts": 50, "comments": 200}
    ],
    "hot_topics": [
      {"topic": "比亚迪", "discussions": 120, "trend": "up"}
    ]
  }
}
```

---

### 6.5 板块管理

---

#### POST /admin/categories — 创建板块

**请求头：** `Authorization: Bearer <token>`（管理员）

**请求体：**
```json
{
  "name": "新股/新债讨论",
  "description": "打新、新股分析讨论区",
  "sort_order": 6
}
```

**成功响应 (201)：**
```json
{
  "code": 201,
  "message": "板块创建成功",
  "data": {
    "id": 6,
    "name": "新股/新债讨论"
  }
}
```

---

#### PUT /admin/categories/{id} — 编辑板块

#### DELETE /admin/categories/{id} — 删除板块

---

## 七、前后端对接规范

### 7.1 前端请求封装示例

```javascript
// frontend/src/api/request.js
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

async function request(url, options = {}) {
  const token = localStorage.getItem('token')
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  }

  // 非 GET 请求自动添加 body 序列化
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }

  const response = await fetch(`${API_BASE}${url}`, config)
  const result = await response.json()

  if (!response.ok) {
    // Token 过期处理
    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    throw new Error(result.message || '请求失败')
  }

  return result.data
}

// 便捷方法
export const api = {
  get: (url, params) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return request(`${url}${query}`, { method: 'GET' })
  },
  post: (url, data) => request(url, { method: 'POST', body: data }),
  put: (url, data) => request(url, { method: 'PUT', body: data }),
  patch: (url, data) => request(url, { method: 'PATCH', body: data }),
  delete: (url) => request(url, { method: 'DELETE' }),
}
```

### 7.2 前端 .env 配置

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 7.3 后端 .env 配置

```env
# backend/.env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=forum_user
MYSQL_PASSWORD=forum_password
MYSQL_DATABASE=stock_fund_forum
JWT_SECRET=your-jwt-secret-key-here
JWT_EXPIRE_HOURS=24
```

---

## 八、数据模型对照

### 8.1 用户 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 用户ID |
| phone | VARCHAR(11) | 手机号 |
| email | VARCHAR(120) | 邮箱 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(50) | 昵称 |
| avatar_url | VARCHAR(500) | 头像 |
| bio | VARCHAR(500) | 简介 |
| role | ENUM | `user` / `moderator` / `admin` |
| auth_level | ENUM | `none` / `basic` / `verified` / `professional` |
| risk_level | ENUM | `conservative` / `moderate` / `aggressive` |
| status | ENUM | `active` / `disabled` |

### 8.2 帖子 (posts)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 帖子ID |
| user_id | BIGINT FK | 作者ID |
| category_id | BIGINT FK | 板块ID |
| title | VARCHAR(120) | 标题 |
| content | TEXT | 内容 |
| post_type | ENUM | `normal` / `long_article` / `poll` / `moment` |
| status | ENUM | `draft` / `published` / `reviewing` / `rejected` |
| view_count | INT | 浏览次数 |
| like_count | INT | 点赞数 |
| comment_count | INT | 评论数 |

### 8.3 评论 (comments)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 评论ID |
| post_id | BIGINT FK | 所属帖子 |
| user_id | BIGINT FK | 评论者 |
| parent_id | BIGINT FK NULL | 父评论ID |
| content | TEXT | 评论内容 |
| like_count | INT | 点赞数 |

---

## 九、API 端点总览

| 模块 | 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|------|
| **用户** | POST | /auth/register | 注册 | N |
| | POST | /auth/send-code | 发送验证码 | N |
| | POST | /auth/login | 登录 | N |
| | POST | /auth/refresh | 刷新Token | Y |
| | GET | /auth/me | 获取当前用户信息 | Y |
| | PUT | /auth/profile | 更新个人资料 | Y |
| | POST | /auth/certification | 实名认证 | Y |
| | POST | /auth/risk-assessment | 风险评估 | Y |
| | GET | /auth/risk-assessment/questions | 获取风险问卷 | Y |
| | GET | /auth/risk-assessment/history | 评估历史记录 | Y |
| **内容** | GET | /categories | 板块列表 | N |
| | GET | /posts | 帖子列表 | N |
| | GET | /posts/{id} | 帖子详情 | N |
| | POST | /posts | 创建帖子 | Y |
| | PUT | /posts/{id} | 编辑帖子 | Y |
| | DELETE | /posts/{id} | 删除帖子 | Y |
| | POST | /posts/{id}/vote | 投票 | Y |
| | GET | /posts/{id}/comments | 评论列表 | N |
| | POST | /posts/{id}/comments | 发表评论 | Y |
| | POST | /posts/{id}/like | 点赞/取消 | Y |
| | POST | /posts/{id}/collect | 收藏/取消 | Y |
| | POST | /posts/{id}/share | 转发 | Y |
| | GET | /users/me/collections | 收藏列表 | Y |
| **社交** | POST | /users/{id}/follow | 关注/取消 | Y |
| | GET | /users/{id}/followers | 粉丝列表 | N |
| | GET | /users/{id}/following | 关注列表 | N |
| | PUT | /users/me/starred | 设置星标 | Y |
| | POST | /groups | 创建群组 | Y |
| | GET | /groups | 群组列表 | N |
| | POST | /groups/{id}/join | 加入群组 | Y |
| | POST | /groups/{id}/members/approve | 审核成员 | Y |
| | GET | /messages | 私信列表 | Y |
| | POST | /messages | 发送私信 | Y |
| **信息整合** | GET | /feed | 个性化推荐 | Y |
| | GET | /hot | 热榜 | N |
| | GET | /search | 搜索 | N |
| | GET | /search/suggestions | 搜索联想 | N |
| **管理** | GET | /admin/review-queue | 审核队列 | Admin |
| | POST | /admin/review-queue/{id}/review | 审核操作 | Admin |
| | POST | /report | 举报 | Y |
| | GET | /admin/users | 用户列表 | Admin |
| | POST | /admin/users/{id}/ban | 封禁用户 | Admin |
| | GET | /admin/stats/overview | 数据总览 | Admin |
| | GET | /admin/stats/trend | 趋势数据 | Admin |
| | POST | /admin/categories | 创建板块 | Admin |
| | PUT | /admin/categories/{id} | 编辑板块 | Admin |
| | DELETE | /admin/categories/{id} | 删除板块 | Admin |
| **系统** | GET | /health | 健康检查 | N |

---

*本文档基于 OpenAPI 3.0 规范组织，可由 FastAPI 自动生成 Swagger UI 交互式文档（`/docs`）。*

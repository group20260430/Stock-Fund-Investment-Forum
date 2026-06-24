# 后端API接口文档 (Backend API)

> 项目：股票基金投资论坛
> 阶段：模块2 — AI辅助设计
> 迭代次数：3 轮
> 规范：OpenAPI 3.0.3（完整规范见 openapi.yaml）

---

## 迭代记录

| 迭代 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-05-18 | 初始API设计，基于用户故事确定核心端点 |
| V1.1 | 2026-05-20 | 细化请求/响应格式，补充错误码和分页规范 |
| V1.2 | 2026-05-22 | 最终版本，补充管理后台API和权限说明 |

---

## 1. API概览

### 1.1 基本信息

| 项目 | 内容 |
|------|------|
| 基础URL | `http://localhost:8000/api`（开发） |
| 协议 | HTTP |
| 数据格式 | JSON |
| 认证方式 | JWT Bearer Token（Header: `Authorization: Bearer {token}`） |
| 分页参数 | `page`（从1开始）, `page_size`（默认20，最大100） |
| 开发文档 | Swagger UI: `http://localhost:8000/docs` |

### 1.2 响应格式

```json
// 成功
{ "code": 200, "message": "success", "data": { ... } }

// 分页
{ "code": 200, "message": "success", "data": { "items": [], "total": 0, "page": 1, "page_size": 20 } }

// 错误
{ "detail": "错误描述" }
```

### 1.3 HTTP状态码约定

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 | 成功 | GET/PUT请求成功 |
| 201 | 创建成功 | POST请求成功 |
| 400 | 请求错误 | 参数校验失败 |
| 401 | 未认证 | Token无效/过期 |
| 403 | 无权限 | 越权操作 |
| 404 | 资源不存在 | 资源未找到 |
| 409 | 冲突 | 重复注册/操作 |
| 422 | 校验错误 | 请求体格式错误 |
| 429 | 频率限制 | 请求太频繁 |
| 500 | 服务器错误 | 内部异常 |

---

## 2. V1.0 — 核心API设计

### 2.1 用户系统

#### POST /api/auth/register — 手机号注册
```
请求体: {
  "phone": "13800138000",        // 必填, 11位手机号
  "password": "Abc@123456",      // 必填, ≥8位, 含字母+数字
  "nickname": "昵称",            // 可选, 不传自动生成
  "avatar_url": null,            // 可选
  "register_type": "phone"       // 可选, 默认phone
}
响应 201: {
  "user_id": 1,
  "token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 7200,
  "user": { ... }
}
错误: 409 手机号已注册, 422 参数校验失败
```

#### POST /api/auth/email/send-code — 发送邮箱验证码
```
请求体: {"email":"user@example.com","type":"register"}
type可选值: register
响应 200: { "expire_in": 300 }
```

#### POST /api/auth/email/verify-code — 验证邮箱验证码
```
请求体: {"email":"user@example.com","code":"123456","code_type":"register"}
响应 200: { "verified": true }
```

#### POST /api/auth/email/register — 邮箱注册
```
请求体: {"email":"user@example.com","password":"Abc@123456","code":"123456","nickname":"昵称"}
响应 201: { "user_id": 1, "token": "eyJ...", ... }
```

#### POST /api/auth/send-code — 发送手机验证码
```
请求体: {"phone":"13800138000","type":"register"}
type可选值: register / login / reset_password
响应 200: { "expire_in": 300, "dev_code": "123456" }  // dev_code仅开发模式返回
错误: 409 手机号已注册(register类型), 404 手机号未注册(login类型)
```

#### POST /api/auth/login — 登录
```
密码登录: {"phone":"13800138000","password":"Abc@123456","login_type":"password"}
验证码登录: {"phone":"13800138000","code":"123456","login_type":"code"}
响应 200: { "token": "eyJ...", "refresh_token": "eyJ...", "expires_in": 7200, "user": {...} }
错误: 401 密码/验证码错误, 404 用户不存在, 403 账号封禁
```

#### POST /api/auth/refresh — 刷新Token
```
请求体: {"refresh_token": "eyJ..."}
响应 200: { "token": "eyJ...", "refresh_token": "eyJ...", "expires_in": 7200 }
错误: 401 Token无效/已吊销
```

#### GET /api/auth/me — 获取当前用户
```
Headers: Authorization: Bearer {token}
响应 200: { "data": { "id":1, "nickname":"...", "phone":"...", ... } }
```

#### PUT /api/auth/profile — 更新个人资料
```
Headers: Authorization: Bearer {token}
请求体: {"nickname":"新昵称","bio":"新简介","avatar_url":"url","tags":[],"favorite_markets":[]}
响应 200: { "data": { ... 更新后的用户信息 } }
```

#### GET/PUT /api/auth/privacy — 隐私设置
```
Headers: Authorization: Bearer {token}
隐私结构: {
  "profile_visibility": "public",       // public/followers_only/private
  "message_permission": "everyone",     // everyone/followers_only/none
  "show_investment_info": true,
  "show_follow_lists": true,
  "show_activity_status": true
}
```

### 2.2 内容系统

#### GET /api/categories — 板块列表
```
响应 200: { "data": [ { "id":1, "name":"股票讨论区", "children":[...] } ] }
```

#### GET /api/posts — 帖子列表
```
参数: category_id, user_id, keyword, sort_by(latest/hot/trending), page, page_size
响应 200: { "data": { "items": [...], "total": 100, "page": 1, "page_size": 20 } }
```

#### POST /api/posts — 创建帖子
```
Headers: Authorization: Bearer {token}
请求体(normal): {"category_id":1,"title":"标题","content":"内容","post_type":"normal","tags":[]}
请求体(poll):   {"category_id":1,"title":"投票","content":"...","post_type":"poll","vote_options":[{"label":"看多"},{"label":"看空"}]}
请求体(longtext): {"category_id":1,"title":"长文","content":"...","post_type":"longtext","cover_image":"url"}
请求体(realtime): {"category_id":1,"title":"实时","content":"...","post_type":"realtime","is_live":true}
响应 201: { "data": { "id": 1, "title": "...", ... } }
```

#### GET /api/posts/{id} — 帖子详情
```
响应 200: { "data": { "id":1, "title":"...", "content":"...", "attachments":[], "vote_options":[], ... } }
```

#### PUT /api/posts/{id} — 编辑帖子
```
Headers: Authorization: Bearer {token}
请求体: { "title":"新标题", "content":"新内容", "post_type":"normal", ... }
错误: 403 非作者编辑
```

#### DELETE /api/posts/{id} — 删除帖子
```
Headers: Authorization: Bearer {token}
错误: 403 非作者删除
```

### 2.3 互动系统

#### GET /api/posts/{id}/comments — 评论列表
```
响应 200: { "data": [ { "id":1, "content":"...", "children":[...] } ] }
```

#### POST /api/posts/{id}/comments — 发表评论
```
Headers: Authorization: Bearer {token}
一级评论: {"content":"好文章！"}
楼中楼:  {"content":"同意","parent_id":1,"reply_to":1}
```

#### POST /api/posts/{id}/like — 帖子点赞/取消
```
Headers: Authorization: Bearer {token}
响应 200: { "data": { "liked": true, "like_count": 124 } }
```

#### POST /api/posts/{id}/collect — 收藏/取消
```
Headers: Authorization: Bearer {token}
请求体: {"folder_id":1}
```

#### POST /api/posts/{id}/share — 转发
```
Headers: Authorization: Bearer {token}
请求体: {"content":"推荐"}
```

### 2.4 社交系统

#### POST /api/users/{id}/follow — 关注/取消
```
Headers: Authorization: Bearer {token}
响应 200: { "data": { "following": true } }
```

#### GET /api/users/me/followers — 我的粉丝
#### GET /api/users/me/following — 我的关注
#### GET /api/users/{id}/followers — 他人粉丝列表
#### GET /api/users/{id}/following — 他人关注列表

#### PUT /api/users/me/starred — 星标用户
```
请求体: {"user_id":2,"starred":true}
```

### 2.5 群组系统

#### POST /api/groups — 创建群组
```
Headers: Authorization: Bearer {token}
请求体: {"name":"群名","description":"...","is_public":true,"need_approval":false}
```

#### POST /api/groups/{id}/join — 加入群组
```
Headers: Authorization: Bearer {token}
公开群直接加入，私密群申请加入（status=pending）
```

#### POST /api/groups/{id}/leave — 退出群组
```
Headers: Authorization: Bearer {token}
错误: 群主不能退出（需先转让或解散）
```

#### DELETE /api/groups/{id} — 解散群组
```
Headers: Authorization: Bearer {token}（群主）
所有成员收到群组解散通知
```

#### PUT /api/groups/{id} — 编辑群组
```
Headers: Authorization: Bearer {token}（群主）
请求体: {"name":"新名称","description":"...","is_public":true}
```

#### DELETE /api/groups/{id}/members/{uid} — 移出成员
```
Headers: Authorization: Bearer {token}（群主/管理员）
错误: 不能移出群主
```

#### POST /api/groups/{id}/members/approve — 审核成员
```
请求体: {"user_id":5,"action":"approved"}  // approved/rejected
```

#### DELETE /api/messages/{id} — 删除消息
```
Headers: Authorization: Bearer {token}（仅发送者可删）
```

#### GET /api/messages/unread-count — 未读私信数
```
Headers: Authorization: Bearer {token}
响应 200: { "data": { "count": 5 } }
```

### 2.6 发现搜索

#### GET /api/feed — 个性化Feed
#### GET /api/hot — 热榜（参数: period=day/week/month）
#### GET /api/search — 全文搜索（参数: keyword, search_type=post/user/stock/group）
#### GET /api/search/suggestions — 搜索联想（参数: q）

### 2.7 行情数据

#### GET /api/market/indices — 实时指数行情
```
响应 200: { "data": [{"code":"000001.SH","name":"上证指数","price":3200.50,"change_pct":0.85}] }
```

#### GET /api/market/kline/{secid} — K线数据（参数: period=daily/weekly/monthly/5min）

### 2.8 通知

#### GET /api/notifications — 通知列表
#### PUT /api/notifications/read — 标记已读
#### GET /api/notifications/unread-count — 未读数

---

## 3. V1.1 — 细化迭代

### 3.1 分页规范统一

```
所有列表接口统一使用以下分页参数和返回格式：

请求参数: page (int, 默认1), page_size (int, 默认20, 最大100)
响应格式: {
  "items": [...],
  "total": 150,        // 总数
  "page": 2,           // 当前页
  "page_size": 20,     // 每页数
  "total_pages": 8     // 总页数
}
```

### 3.2 错误响应规范

```json
{
  "detail": {
    "message": "用户友好的错误描述",
    "code": "DUPLICATE_PHONE",     // 错误码
    "field": "phone"               // 关联字段（可选）
  }
}
```

### 3.3 Token认证流程

```
客户端 → POST /auth/login          → 获得 access_token + refresh_token
客户端 → POST /auth/refresh        → 刷新 access_token（旧refresh_token被吊销）
客户端 → GET /auth/me (带Token)    → 获取用户信息
客户端 → 401 响应                  → 自动尝试刷新Token → 失败则跳转登录
```

---

## 4. V1.2 — 最终版本补充

### 4.1 管理后台API

#### POST /api/report — 提交举报
```
请求体: {"target_type":"post","target_id":1,"reason":"违规内容","description":"..."}
```

#### GET /api/admin/review-queue — 审核队列
```
Headers: Authorization: Bearer {管理员Token}
参数: status=pending, type=post/comment, page, page_size
```

#### POST /api/admin/review-queue/{id}/review — 执行审核
```
请求体: {"action":"approved","review_comment":"合规"}  // approved/rejected
```

#### GET /api/admin/users — 用户列表
#### POST /api/admin/users/{id}/ban — 封禁/解封
```
封禁: {"action":"ban","reason":"违规","duration_hours":72}
解封: {"action":"unban"}
```

#### GET /api/admin/stats/overview — 数据总览
#### GET /api/admin/stats/trend — 趋势数据（参数: period）
#### GET /api/admin/stats/hot-topics — 热门话题深度分析
#### GET /api/admin/stats/engagement — 用户参与度报告

#### GET /api/admin/reports — 举报列表
#### POST /api/admin/reports/{id} — 处理举报

#### GET /api/admin/certifications — 认证审核列表
#### POST /api/admin/certifications/{id}/review — 审核实名认证
```
请求体: {"action":"approved","review_comment":"通过"}
```

#### GET /api/admin/professional-certifications — 专业认证列表
#### POST /api/admin/professional-certifications/{id}/review — 审核专业认证

#### GET /api/admin/sensitive-words — 敏感词列表
#### POST /api/admin/sensitive-words — 添加敏感词
```
请求体: {"word":"禁词","level":"block","category":"政治"}
```
#### DELETE /api/admin/sensitive-words/{id} — 删除敏感词

#### GET /api/admin/compliance/rules — 合规规则列表
#### POST /api/admin/compliance/rules — 创建合规规则
```
请求体: {"name":"荐股检测","pattern":"推荐.*买入|拉升.*股票","category":"market","level":"block"}
```
#### DELETE /api/admin/compliance/rules/{id} — 删除合规规则
#### POST /api/admin/compliance/check — 合规检查

#### GET /api/admin/activity-logs — 操作日志

#### POST /api/admin/duplicate-content/scan — 扫描重复内容
#### GET /api/admin/duplicate-content/stats — 重复内容统计

#### GET /api/admin/behavior/user-summary — 用户行为汇总
#### GET /api/admin/behavior/user/{id}/timeline — 用户活动时间线
#### GET /api/admin/behavior/suspicious — 异常用户检测

#### POST /api/admin/categories — 新增板块
```
请求体: {"name":"新区块","description":"...","parent_id":null,"sort_order":1}
```

#### PUT /api/admin/categories/{id} — 编辑板块
#### DELETE /api/admin/categories/{id} — 删除板块
#### POST /api/admin/categories/reorder — 重新排序板块

### 4.2 文件上传

#### POST /api/uploads — 上传文件
```
Headers: Authorization: Bearer {token}, Content-Type: multipart/form-data
参数: file (文件), upload_type (avatar/post_image/certification)
限制: 最大10MB, 允许类型: image/jpeg, image/png, image/gif, application/pdf
响应 200: { "data": { "url": "https://...", "file_name": "abc.jpg", "file_size": 1024 } }
```

### 4.3 API安全规范

| 安全要求 | 说明 |
|---------|------|
| 认证 | 除登录/注册外，敏感操作需要JWT Token |
| 权限 | 资源操作验证所有者身份（如删帖需要是作者） |
| 角色 | 管理接口仅管理员可访问（role=admin） |
| 频率限制 | 验证码发送60秒内限制一次 |
| 输入校验 | 所有输入经Pydantic schema校验 |
| 文件上传 | MIME类型白名单 + 大小限制 |
| CORS | 仅允许前端域名跨域访问 |

### 4.4 API端点完整列表

| 方法 | 路径 | 权限 | 描述 |
|------|------|------|------|
| POST | /auth/register | 公开 | 手机号注册 |
| POST | /auth/email/send-code | 公开 | 发送邮箱验证码 |
| POST | /auth/email/verify-code | 公开 | 验证邮箱验证码 |
| POST | /auth/email/register | 公开 | 邮箱注册 |
| POST | /auth/send-code | 公开 | 发送手机验证码 |
| POST | /auth/verify-code | 公开 | 验证手机验证码 |
| POST | /auth/reset-password | 公开 | 重置密码 |
| POST | /auth/login | 公开 | 登录 |
| POST | /auth/refresh | 公开 | 刷新Token |
| GET | /auth/me | 登录 | 获取当前用户 |
| PUT | /auth/profile | 登录 | 更新资料 |
| GET | /auth/privacy | 登录 | 获取隐私设置 |
| PUT | /auth/privacy | 登录 | 更新隐私设置 |
| POST | /auth/certification | 登录 | 实名认证申请 |
| POST | /auth/professional-certification | 登录 | 专业认证申请 |
| POST | /auth/risk-assessment | 登录 | 提交风险评估 |
| GET | /auth/risk-assessment/questions | 登录 | 获取评估题目 |
| GET | /auth/risk-assessment/history | 登录 | 评估历史记录 |
| GET | /auth/points/history | 登录 | 积分变动记录 |
| GET | /categories | 公开 | 板块列表 |
| GET | /posts | 公开 | 帖子列表 |
| POST | /posts | 登录 | 创建帖子 |
| GET | /posts/{id} | 公开 | 帖子详情 |
| PUT | /posts/{id} | 登录 | 编辑帖子 |
| DELETE | /posts/{id} | 登录 | 删除帖子 |
| POST | /posts/{id}/vote | 登录 | 投票 |
| GET | /posts/{id}/comments | 公开 | 评论列表 |
| POST | /posts/{id}/comments | 登录 | 发表评论 |
| DELETE | /comments/{id} | 登录 | 删除评论 |
| POST | /comments/{id}/like | 登录 | 评论点赞 |
| POST | /posts/{id}/like | 登录 | 帖子点赞 |
| POST | /posts/{id}/collect | 登录 | 收藏帖子 |
| GET | /users/me/collections | 登录 | 我的收藏 |
| POST | /posts/{id}/share | 登录 | 转发帖子 |
| GET | /users/{id} | 公开 | 用户资料 |
| POST | /users/{id}/follow | 登录 | 关注/取消关注 |
| GET | /users/me/followers | 登录 | 我的粉丝列表 |
| GET | /users/me/following | 登录 | 我的关注列表 |
| GET | /users/{id}/followers | 公开 | 他人粉丝列表 |
| GET | /users/{id}/following | 公开 | 他人关注列表 |
| PUT | /users/me/starred | 登录 | 星标用户设置 |
| GET | /users/{id}/points | 公开 | 用户积分/等级 |
| POST | /groups | 登录 | 创建群组 |
| GET | /groups | 登录 | 群组列表 |
| GET | /groups/{id} | 登录 | 群组详情 |
| POST | /groups/{id}/join | 登录 | 加入群组 |
| POST | /groups/{id}/leave | 登录 | 退出群组 |
| DELETE | /groups/{id} | 登录 | 解散群组 |
| PUT | /groups/{id} | 登录 | 编辑群组 |
| POST | /groups/{id}/posts | 登录 | 群内发帖 |
| GET | /groups/{id}/posts | 登录 | 群内帖子 |
| POST | /groups/{id}/members/approve | 登录 | 审核成员 |
| DELETE | /groups/{id}/members/{uid} | 登录 | 移出成员 |
| POST | /messages | 登录 | 发送消息 |
| GET | /messages | 登录 | 消息列表 |
| DELETE | /messages/{id} | 登录 | 删除消息 |
| GET | /messages/unread-count | 登录 | 未读私信数 |
| GET | /feed | 公开 | 个性化Feed |
| GET | /hot | 公开 | 热榜 |
| GET | /search | 公开 | 搜索 |
| GET | /search/suggestions | 公开 | 搜索联想 |
| GET | /market/indices | 公开 | 实时行情 |
| GET | /market/kline/{secid} | 公开 | K线数据 |
| GET | /notifications | 登录 | 通知列表 |
| PUT | /notifications/read | 登录 | 标记已读 |
| GET | /notifications/unread-count | 登录 | 未读数 |
| POST | /report | 登录 | 举报 |
| GET | /admin/review-queue | 管理员 | 审核队列 |
| POST | /admin/review-queue/{id}/review | 管理员 | 执行审核 |
| GET | /admin/users | 管理员 | 用户列表 |
| POST | /admin/users/{id}/ban | 管理员 | 封禁/解封 |
| GET | /admin/stats/overview | 管理员 | 数据总览 |
| GET | /admin/stats/trend | 管理员 | 趋势数据 |
| GET | /admin/stats/hot-topics | 管理员 | 热门话题分析 |
| GET | /admin/stats/engagement | 管理员 | 用户参与度报告 |
| GET | /admin/reports | 管理员 | 举报列表 |
| POST | /admin/reports/{id} | 管理员 | 处理举报 |
| GET | /admin/certifications | 管理员 | 认证审核列表 |
| POST | /admin/certifications/{id}/review | 管理员 | 审核实名认证 |
| GET | /admin/professional-certifications | 管理员 | 专业认证列表 |
| POST | /admin/professional-certifications/{id}/review | 管理员 | 审核专业认证 |
| GET | /admin/sensitive-words | 管理员 | 敏感词列表 |
| POST | /admin/sensitive-words | 管理员 | 添加敏感词 |
| DELETE | /admin/sensitive-words/{id} | 管理员 | 删除敏感词 |
| GET | /admin/compliance/rules | 管理员 | 合规规则列表 |
| POST | /admin/compliance/rules | 管理员 | 创建合规规则 |
| DELETE | /admin/compliance/rules/{id} | 管理员 | 删除合规规则 |
| POST | /admin/compliance/check | 管理员 | 合规检查 |
| GET | /admin/activity-logs | 管理员 | 操作日志 |
| POST | /admin/duplicate-content/scan | 管理员 | 扫描重复内容 |
| GET | /admin/duplicate-content/stats | 管理员 | 重复内容统计 |
| GET | /admin/behavior/user-summary | 管理员 | 用户行为汇总 |
| GET | /admin/behavior/user/{id}/timeline | 管理员 | 用户活动时间线 |
| GET | /admin/behavior/suspicious | 管理员 | 异常用户检测 |
| POST | /admin/categories/reorder | 管理员 | 重新排序板块 |
| POST | /admin/categories | 管理员 | 新增板块 |
| PUT | /admin/categories/{id} | 管理员 | 编辑板块 |
| DELETE | /admin/categories/{id} | 管理员 | 删除板块 |
| POST | /uploads | 登录 | 上传文件 |
| GET | /health | 公开 | 健康检查 |

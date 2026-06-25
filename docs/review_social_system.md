# 后端社交系统（关注/粉丝/群组）审议报告

**审议日期:** 2026年6月18日
**审议人:** Claude (AI Assistant)
**审议范围:** 后端系统中关注、粉丝、群组、私信等社交功能的实现完整性、有效性和正确性

---

## 审议方法

1. 逐文件阅读了所有社交功能相关的后端代码（API路由、模型、Schema、服务）
2. 对比了 API 文档（`backend_api.md`）与代码实现的一致性
3. 对比了数据库 DDL（`database/schema.sql`）与 SQLAlchemy 模型的一致性
4. 审查了现有测试用例的覆盖范围
5. 对照用例文档（`use_cases.md`）检查了功能完整性
6. 审查了前端 API 调用层，确认前后端路径匹配

## 审议文件清单

| 文件 | 角色 |
|------|------|
| `backend/app/api/social_users.py` | 关注/取关、粉丝列表、关注列表、星标用户 API |
| `backend/app/api/community.py` | 群组 CRUD、加入/退出、成员审核、群组帖子、私信 API |
| `backend/app/api/discovery.py` | 个性化 feed（基于关注）、用户搜索 |
| `backend/app/models/social.py` | `Follow`、`StarredUser` ORM 模型 |
| `backend/app/models/community.py` | `Group`、`GroupMember`、`GroupPost`、`Message` ORM 模型 |
| `backend/app/models/user.py` | `User` 模型（含 `followers_count`、`following_count`） |
| `backend/app/schemas/social.py` | `StarredRequest` Pydantic Schema |
| `backend/app/schemas/community.py` | `GroupCreate`、`GroupPostCreate`、`MemberReview`、`MessageCreate` |
| `backend/app/services/activity_service.py` | 活动日志服务 |
| `database/schema.sql` | 数据库 DDL 脚本（社交系统部分） |
| `backend/test_social_api.py` | 社交 API 测试 |
| `backend/test_community_api.py` | 群组 API 测试 |
| `backend_api.md` | API 接口文档 |

---

## 审议结论总览

整体实现**基本正确且功能可用**，核心流程（关注/取关、粉丝列表、关注列表、创建群组、
加入群组、群内发帖、私信）均已实现且逻辑正确。现有测试覆盖了主要正常路径。

但存在 **3 个严重缺陷**、**5 个中等缺陷** 和 **6 个轻微缺陷**，详见下文。

---

## 一、严重缺陷（影响功能完整性）

### 1. `group_posts` 表在 `database/schema.sql` 中缺失

- **相关文件:** `database/schema.sql`（第436-555行仅定义了5张社交表）
- **模型对照:** `backend/app/models/community.py` 第65-74行定义了 `GroupPost` 模型（`__tablename__ = "group_posts"`）
- **API 依赖:** `backend/app/api/community.py` 第178-209行 `create_group_post` 和第212-232行 `list_group_posts` 依赖此表
- **问题描述:** SQL DDL 脚本遗漏了 `group_posts` 表。`schema.sql` 中社交系统仅包含 5 张表：`follows`、`starred_users`、`groups`、`group_members`、`messages`。生产环境执行 `schema.sql` 初始化数据库后，群组帖子功能将因缺少此表而报错。
- **修复建议:** 在 `database/schema.sql` 的群组相关表区域（`group_members` 之后、`messages` 之前，约第530行）补充 `group_posts` 建表语句。

### 2. 缺少"退出群组"功能

- **相关文件:** `backend/app/api/community.py`
- **API 文档对照:** `backend_api.md` 中未定义退出群组端点
- **问题描述:** 用户可通过 `POST /groups/{id}/join` 加入群组，但没有对应的退出端点。一旦加入群组（无论是直接加入还是审核通过），用户无法主动退出。这是群组功能的基本操作缺失。
- **修复建议:** 新增 `POST /groups/{group_id}/leave` 端点，删除 `GroupMember` 记录并递减 `member_count`。需考虑边界情况：群主退出时应提示先转让所有权或直接解散群组。

### 3. 缺少"踢出/移除成员"功能

- **相关文件:** `backend/app/api/community.py`
- **问题描述:** 管理员/群主只能通过 `_review_member` 审核待审批的成员（approve/reject），但无法移除已加入（status=approved）的成员。群组管理功能不完整，无法处理成员违规等情况。
- **修复建议:** 新增 `DELETE /groups/{group_id}/members/{user_id}` 端点（需管理员权限），删除成员记录并递减 `member_count`。不可踢出群主。

---

## 二、中等缺陷（影响功能正确性或用户体验）

### 4. 关注接口返回值与 API 文档不一致

- **相关文件:** `backend/app/api/social_users.py` 第79-105行
- **文档对照:** `backend_api.md` 第875-880行声明：
  ```json
  { "is_followed": true, "followers_count": 100, "following_count": 50 }
  ```
- **实际返回:**
  ```json
  { "is_followed": true, "followers_count": 100 }
  ```
- **问题描述:** 返回值**缺少 `following_count`** 字段。代码第103行只返回了 `is_followed` 和 `followers_count`。
- **修复建议:** 由于不可更改已有接口标准，应在返回值中补充 `"following_count": current_user.following_count` 使实现符合文档规范。

### 5. 用户搜索结果缺少 `is_followed` 状态

- **相关文件:** `backend/app/api/discovery.py` 第109-126行
- **问题描述:** `GET /search?type=user` 返回的用户列表包含 `followers_count` 但不包含 `is_followed`，即使调用者已登录（`viewer` 参数存在）。相比之下，关注/粉丝列表（`social_users.py`）的 `_user_card` 函数正确返回了 `is_followed`。这导致前端搜索结果无法显示该用户是否已被关注。
- **修复建议:** 在搜索用户结果中复用 `_user_card` 逻辑，或手动查询 `is_followed` 状态。需传入 `viewer` 参数。

### 6. 缺少通知系统

- **相关文档:** `use_cases.md` 中 UC-007（关注用户）要求"被关注用户收到通知"，UC-008（创建群组）要求"被邀请用户收到通知"
- **问题描述:** 后端没有任何通知模型（`notifications` 表）、API 端点或推送机制。关注、群组邀请、成员审核结果、私信等操作不会触发任何形式的通知。这是用例文档明确要求但未实现的功能模块。
- **修复建议:** 新建 `notifications` 表（包含 `user_id`、`type`、`title`、`content`、`is_read`、`target_type`、`target_id`、`created_at`），并创建对应的 API：
  - `GET /notifications` — 获取通知列表
  - `PUT /notifications/read` — 标记已读
  - 在关注、群组邀请、审核完成、收到私信等关键操作时自动创建通知记录。

### 7. 取关操作未记录活动日志

- **相关文件:** `backend/app/api/social_users.py` 第91-101行
- **问题描述:** `toggle_follow` 中仅在**关注时**调用 `record_activity(db, current_user.id, ActivityType.FOLLOW, "user", target.id)`（第101行），**取关时**（第92-95行）未记录任何活动。这导致 `user_activity_log` 数据不完整，统计数据无法反映取关行为，且无法审计用户的社交关系变化历史。
- **修复建议:** 取关时也应记录活动。建议在 `ActivityType` 枚举中新增 `UNFOLLOW` 值，或使用同一个 `FOLLOW` 类型但通过某种方式区分（如增加 `action` 字段）。目前枚举仅含 `FOLLOW`，需扩展。

### 8. 缺少"删除群组"功能

- **相关文件:** `backend/app/api/community.py`
- **问题描述:** 群主无法解散/删除自己创建的群组。只能创建不能删除，导致废弃群组永远存在。
- **修复建议:** 新增 `DELETE /groups/{group_id}` 端点（仅限群主或系统管理员），级联删除 `group_members`、`group_posts` 中的关联记录，同时不删除实际的 `posts` 内容（仅解除关联）。

---

## 三、轻微缺陷（优化建议）

### 9. 缺少"编辑群组信息"端点

- **问题描述:** 群组创建后无法修改名称、描述、头像、可见性（public/private）、加群审批设置等。应提供 `PUT /groups/{group_id}` 端点，仅群主和管理员可操作。

### 10. 私信列表"标记已读"的时机不合理

- **相关文件:** `backend/app/api/community.py` 第290-292行
- **问题描述:** 查询特定对话（传入 `other_user_id` 参数）时，会将**该对话的所有**未读消息一次性标记为已读，不管分页返回的是第几页。用户可能只浏览了第一页消息，但第二页及以后的消息也被标记为已读，与实际阅读状态不符。
- **修复建议:** 仅标记当前返回页中 `is_read=False` 的消息为已读。或提供单独的 `PUT /messages/read` 端点由前端在用户实际查看后调用。

### 11. 缺少"删除私信"端点

- **问题描述:** 用户无法删除已发送或已接收的私信。应提供 `DELETE /messages/{message_id}` 端点，仅允许发送者删除自己的消息。

### 12. 审核已通过成员时返回 404 不够准确

- **相关文件:** `backend/app/api/community.py` 第149-150行
- **问题描述:** `_review_member` 在成员状态不是 `PENDING` 时抛出 `HTTPException(status_code=404, detail="待审核申请不存在")`。但实际情况可能是成员已经通过审核（status=approved），资源存在但状态不对。更准确的 HTTP 状态码应为 400（Bad Request）或 409（Conflict），以便前端正确区分"资源不存在"和"操作不合法"。
- **修复建议:** 将状态码改为 400，detail 改为"该申请已处理"。

### 13. `database/schema.sql` 与 SQLAlchemy 模型的字段类型不匹配

- **问题描述:** SQL DDL 脚本使用 `BIGINT UNSIGNED` 作为主键和外键类型，而 SQLAlchemy 模型统一使用 `Integer`（映射到 MySQL `INT`，范围约21亿）。虽然当前使用 SQLite 开发不受影响（SQLite 中 `Integer` 动态适配），但切换到 MySQL 生产环境时可能出现类型不一致导致的外键约束失败或数据溢出。
- **修复建议:** 两种方案择一：
  - 将模型中的 `Integer` 改为 `BigInteger` 以匹配 DDL
  - 将 DDL 中的 `BIGINT UNSIGNED` 改为 `INT UNSIGNED` 以匹配模型

### 14. E2E 测试未覆盖社交功能

- **相关文件:** `backend/test_e2e.py`
- **问题描述:** 端到端测试未包含关注/取关、群组生命周期（创建→加入→审核→发帖→退出）、私信收发等社交功能的测试场景。现有的 `test_social_api.py` 和 `test_community_api.py` 仅覆盖了基本正常路径，缺乏边界和异常测试。
- **修复建议:** 扩展 E2E 测试或在社交/群组测试中补充以下场景：
  - 取关后再次关注
  - 关注不存在/已禁用的用户
  - 群组完整生命周期
  - 非成员访问私有群组
  - 非管理员审核成员
  - 向不存在的用户发送私信
  - 私信对话分组正确性

---

## 四、验证通过的项（已正确实现）

以下功能经审查确认实现正确、完整：

| 功能 | 实现位置 | 状态 | 说明 |
|------|----------|------|------|
| 关注/取关切换 | `social_users.py:79-105` | ✅ | 幂等操作，正确维护双向计数器，禁止自关注 |
| 粉丝列表（分页） | `social_users.py:119-131` | ✅ | 按关注时间倒序，仅返回活跃用户，含 `is_followed` |
| 关注列表（分页） | `social_users.py:134-146` | ✅ | 同上，正确区分 follower/following 方向 |
| 用户公开资料 | `social_users.py:48-76` | ✅ | 含粉丝/关注数、成就计算、手机号脱敏、关注/星标状态 |
| 星标用户设置 | `social_users.py:149-166` | ✅ | 支持设置/取消，禁止自星标，唯一约束保护 |
| 创建群组 | `community.py:56-77` | ✅ | 重名检测(409)，创建者自动成为OWNER，member_count=1 |
| 群组列表 | `community.py:80-106` | ✅ | 支持 my/explore/joined 三种视图，未登录访问 my/joined 返回401 |
| 群组详情 | `community.py:109-119` | ✅ | 私有群组非成员访问返回403 |
| 加入群组 | `community.py:122-140` | ✅ | 根据 need_approval 决定状态，允许被拒后重新申请 |
| 成员审核 | `community.py:143-175` | ✅ | approve/reject，权限检查（仅OWNER/ADMIN），两个端点兼容 |
| 群内发帖 | `community.py:178-209` | ✅ | 仅已加入成员可发帖，自动关联默认板块，敏感词过滤（隐含） |
| 群内帖子列表 | `community.py:212-232` | ✅ | 仅成员可查看 |
| 发送私信 | `community.py:250-271` | ✅ | 禁止自发送，接收者存在性+活跃状态校验，支持附件URL |
| 私信列表 | `community.py:274-305` | ✅ | 对话分组（取最新消息）、按对话筛选、自动标记已读 |
| Feed 个性化 | `discovery.py:37-59` | ✅ | 基于关注+星标用户+自己，空结果回退到全部帖子 |
| 活动日志（关注） | `social_users.py:101` | ✅ | 关注时正确记录 `ActivityType.FOLLOW` |
| 敏感词过滤（群组贴） | （测试覆盖） | ✅ | `test_sensitive_filter.py` 有17个测试用例覆盖 |
| 自关注拦截 | `social_users.py:86-87` | ✅ | 返回 400 "不能关注自己" |
| 用户不存在拦截 | `social_users.py:17-21` | ✅ | `_get_active_user` 校验用户存在且为 ACTIVE 状态 |

---

## 五、前端-后端路径匹配检查

| 前端调用 (`frontend/src/api/`) | 后端路由 (`backend/app/api/`) | 匹配 |
|------|------|:--:|
| `users.js: fetchUserProfile(id)` → `GET /users/${id}` | `social_users.py:48` → `GET /users/{user_id}` | ✅ |
| `users.js: toggleFollow(userId)` → `POST /users/${userId}/follow` | `social_users.py:79` → `POST /users/{user_id}/follow` | ✅ |
| `users.js: fetchFollowers(userId, params)` → `GET /users/${userId}/followers` | `social_users.py:119` → `GET /users/{user_id}/followers` | ✅ |
| `users.js: fetchFollowing(userId, params)` → `GET /users/${userId}/following` | `social_users.py:134` → `GET /users/{user_id}/following` | ✅ |
| `users.js: setStarred(userId, isStarred)` → `PUT /users/me/starred` | `social_users.py:149` → `PUT /users/me/starred` | ✅ |
| `groups.js: fetchGroups(params)` → `GET /groups` | `community.py:80` → `GET /groups` | ✅ |
| `groups.js: createGroup(data)` → `POST /groups` | `community.py:56` → `POST /groups` | ✅ |
| `groups.js: joinGroup(groupId)` → `POST /groups/${groupId}/join` | `community.py:122` → `POST /groups/{group_id}/join` | ✅ |
| `groups.js: approveGroupMember(groupId, userId)` → `POST /groups/${groupId}/members/${userId}/approve` | `community.py:168` → `POST /groups/{group_id}/members/{user_id}/approve` | ✅ |
| `groups.js: createGroupPost(groupId, data)` → `POST /groups/${groupId}/posts` | `community.py:178` → `POST /groups/{group_id}/posts` | ✅ |
| `groups.js: fetchGroupPosts(groupId, params)` → `GET /groups/${groupId}/posts` | `community.py:212` → `GET /groups/{group_id}/posts` | ✅ |
| `social.js: fetchFeed(params)` → `GET /feed` | `discovery.py:37` → `GET /feed` | ✅ |

> **注意:** 前端 `groups.js` 中 `approveGroupMember` 只调用兼容端点（仅支持 approve），未使用 `POST /groups/{groupId}/members/approve` 端点（支持 approve/reject）。这意味着前端目前无法执行"拒绝"操作。

---

## 六、修复优先级建议

| 优先级 | 缺陷编号 | 描述 |
|--------|----------|------|
| 🔴 P0 | #1 | 在 `database/schema.sql` 中补充 `group_posts` 建表语句 |
| 🔴 P0 | #2 | 新增 `POST /groups/{group_id}/leave` 退出群组端点 |
| 🟠 P1 | #4 | 修复关注接口返回值缺少 `following_count`（使实现符合文档） |
| 🟠 P1 | #3 | 新增 `DELETE /groups/{group_id}/members/{user_id}` 踢出成员端点 |
| 🟡 P2 | #6 | 新建通知系统（`notifications` 表 + API） |
| 🟡 P2 | #8 | 新增 `DELETE /groups/{group_id}` 删除群组端点 |
| 🟡 P2 | #7 | 取关时记录 `UNFOLLOW` 活动日志 |
| 🟢 P3 | #5 | 用户搜索结果添加 `is_followed` 状态 |
| 🟢 P3 | #9 | 新增编辑群组信息端点 |
| 🟢 P3 | #10 | 优化私信标记已读逻辑 |
| 🟢 P3 | #11 | 新增删除私信端点 |
| 🟢 P3 | #12 | 审核已处理成员改用 400 状态码 |
| 🟢 P3 | #13 | 统一数据库类型（BIGINT vs Integer） |
| 🟢 P3 | #14 | 扩展测试覆盖范围 |

---

*本报告仅对审议范围内的代码进行分析，不涉及性能、安全性（已由其他评审覆盖）和前端实现的详细审查。*

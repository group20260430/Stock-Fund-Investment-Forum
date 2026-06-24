# AI 使用文档 (AI Interaction Log)

> 项目：股票基金投资论坛
> 记录周期：2026-04-30 ~ 2026-06-24
> 使用工具：GitHub Copilot (DeepSeek V4 Flash)
> 涵盖模块：需求分析 → 设计 → 编码实现

---

## 目录

1. [模块1：AI辅助需求分析](#模块1ai辅助需求分析)
2. [模块2：AI辅助设计](#模块2ai辅助设计)
3. [模块3：AI辅助编码实现](#模块3ai辅助编码实现)
4. [AI使用技巧总结](#ai使用技巧总结)

---

## 模块1：AI辅助需求分析

### 交互1：生成用户故事

**日期：** 2026-05-06

**原始提示词：**
```
作为产品经理，为【股票基金投资论坛】中如下功能生成用户故事：用户注册登录、帖子发布与管理、评论互动、社交关系、群组社区、搜索发现、行情数据、通知消息、管理后台。
要求用户故事遵循以下格式：作为一名…我想…以便...。
每个功能至少生成2-3个用户故事，覆盖不同角色（访客、注册用户、管理员）。
```

**AI输出摘要：**
生成了16条初始用户故事，涵盖：
- 用户系统：访客注册、用户登录、找回密码、个人资料管理、实名认证
- 内容系统：浏览板块帖子、创建帖子、互动（评论/点赞/收藏）
- 社交系统：关注用户、群组社区、私信沟通
- 发现搜索：搜索内容、热榜推荐
- 管理后台：后台管理

**可能存在的问题：**
1. 缺少专业认证场景（持牌分析师等专业用户需求）
2. 缺少风险评估和积分等级体系
3. 缺少隐私控制需求
4. 缺少内容合规检测（敏感词、重复内容）

**迭代优化：**
```
V1.1优化提示词：
作为产品经理，为【股票基金投资论坛】补充以下遗漏场景的用户故事：
1. 专业用户认证（如持牌分析师）
2. 风险评估问卷
3. 积分与等级体系
4. 内容合规检测（敏感词/合规规则）
5. 重复内容检测
6. 隐私控制设置
要求覆盖访客、注册用户、认证用户、管理员四种角色。
```

**最终成果：** 经过3轮迭代，用户故事从16条扩展到26条，覆盖5大模块的全部功能场景。

---

### 交互2：生成交互场景（用例）

**日期：** 2026-05-10

**原始提示词：**
```
作为软件分析师，为【股票基金投资论坛】的以下用户故事书写交互场景：
US-01 手机号注册：访客想要使用手机号和验证码注册账号，以便快速创建身份参与论坛讨论。
要求遵循以下用例格式：用例名称、对应故事、参与者、前置条件、后置条件、基本流程、备选路径。
需要包含正常流程和至少3个异常流程（验证码错误、手机号已注册、密码强度不足）。
```

**AI输出摘要：**
生成了UC-01用户注册用例，包含：
- 基本流程：11个步骤，从点击注册到自动登录跳转首页
- 备选路径：验证码错误/过期、手机号已注册、密码弱、邮箱注册分支
- 清晰的参与者和条件定义

**可能存在的问题：**
1. 初始版本缺少边界场景（如验证码5分钟过期）
2. 未涉及Token过期处理
3. 缺少并发场景描述（如同一手机号同时请求多个验证码）

**迭代优化：**
```
V1.1优化提示词（批量生成）：
为以下用户故事生成交互场景，每个用例需包含：基本流程+至少3个备选路径+2个异常场景：
US-03登录、US-07浏览板块帖子、US-08创建帖子、US-09评论互动、US-11关注用户、US-12群组管理、US-14搜索内容、US-16后台管理

要求：
- 创建帖子需包含敏感词检测和重复内容检测的备选路径
- 群组管理需区分公开群和私密群的加入流程
- 后台管理需区分管理员和普通用户的权限差异
```

**最终成果：** 生成16个完整用例，每个含基本流程、备选路径、异常场景，覆盖全部功能模块。

---

### 交互3：细化业务需求

**日期：** 2026-05-08

**原始提示词：**
```
对于【股票基金投资论坛】，如何理解以下功能：积分等级体系。

请从以下角度分析：
1. 积分的获取途径有哪些？
2. 等级如何计算和晋升？
3. 积分和等级对用户有什么实际价值？
4. 需要考虑哪些防作弊机制？
```

**AI输出摘要：**
- 积分获取：每日签到(+1)、发帖(+5)、评论(+2)、被点赞(+1)、被转发(+3)、获得粉丝(+1)
- 积分扣除：删帖(-5)、删评论(-2)、取消点赞(-1)、失去粉丝(-1)
- 等级阈值：8级体系（0→L1, 100→L2, 300→L3, 600→L4, 1000→L5, 2000→L6, 5000→L7, 10000→L8）
- 防作弊：每日签到限制、频繁操作检测、异常积分波动告警

**可能存在的问题：**
AI建议的积分值偏小，经团队讨论后将发帖从+3调整为+5，评论从+1调整为+2，以提升用户参与积极性。

**迭代优化：**
```
调整后的积分体系：
- daily_login: +1
- create_post: +5（原建议+3）
- create_comment: +2（原建议+1）
- post_liked: +1
- post_shared: +3
- gained_follower: +1
- delete_post: -5
保持等级阈值不变。
```

---

## 模块2：AI辅助设计

### 交互4：架构设计和技术选型

**日期：** 2026-05-16

**原始提示词：**
```
为一个股票基金投资论坛进行技术选型和架构设计。
需求概述：
- 前后端分离架构
- 用户注册登录（JWT认证）
- 帖子发布（支持普通帖/投票帖/长文帖）
- 评论（支持楼中楼）
- 社交关系（关注/粉丝）
- 群组社区
- 实时行情数据（从外部API获取）
- 管理后台
- 敏感词检测和内容审核

请推荐技术栈并说明理由，给出项目目录结构建议。
```

**AI输出摘要：**
- 推荐技术栈：Vue 3 + FastAPI + MySQL 8.0 + SQLAlchemy
- 前后端分离架构图
- 详细的项目目录结构（前端按功能模块分，后端按三层架构分）
- 认证方案：JWT + Refresh Token Rotation

**可能存在的问题：**
1. AI推荐使用 PostgreSQL，但团队更熟悉 MySQL，修改为 MySQL 8.0
2. AI建议使用 Celery 做异步任务，考虑到项目规模取消，改用简单同步处理

**迭代优化：**
```
V1.1优化：
- 数据库：PostgreSQL → MySQL 8.0（团队熟悉度优先）
- 异步任务：Celery → 同步处理（项目规模小，无需消息队列）
- 增加：行情数据源降级策略（东方财富→新浪→空数据）
- 增加：文件上传模块（MIME类型白名单+大小限制）
```

---

### 交互5：数据库ER图设计

**日期：** 2026-05-18

**原始提示词：**
```
根据以下需求描述，提取类及其属性和操作，生成数据库ER图。

需求：
1. 用户可以注册（手机号/邮箱），登录，修改个人资料
2. 用户可以创建帖子（普通/投票/长文/实时），编辑和删除自己的帖子
3. 用户可以对帖子发表评论，评论支持楼中楼回复
4. 用户可以点赞帖子和评论，收藏帖子，转发帖子
5. 用户可以关注其他用户
6. 用户可以创建和加入投资群组，在群内发帖
7. 用户可以发送私信
8. 帖子属于某个板块，板块支持树形结构
9. 帖子可以包含多个投票选项，用户可以投票
10. 管理员可以审核内容、管理用户、管理板块

请用Mermaid ER图格式输出，标注主键和外键。
```

**AI输出摘要：**
生成了完整的ER图，包含15个核心实体及其关系：
- User ↔ Post（一对多）、Post ↔ Comment（一对多）
- Category 自引用（树形结构）
- Comment 自引用（楼中楼）
- User ↔ Follow（复合主键）
- Group ↔ GroupMember（多对多）
- Like 多态设计（target_type区分帖子/评论）

**可能存在的问题：**
1. 初始版本未包含积分表和运营管理表
2. 缺少全文索引设计
3. 软删除 vs 硬删除未明确

**迭代优化：**
```
V1.1补充：
- 增加：points_history 积分历史表
- 增加：sensitive_words 敏感词表，compliance_rules 合规规则表
- 增加：daily_stats 每日统计表，user_activity_log 活动日志表
- 增加：professional_certifications 专业认证表
- 增加：posts 表 FULLTEXT INDEX（title, content）
- 明确：采用状态字段（published/review/banned）而非物理删除

V1.2优化：
- 增加：privacy_settings JSON字段到users表
- 增加：notifications 独立表，10种通知类型
- 优化：所有表添加 created_at/updated_at 时间戳
- 优化：点赞采用 UNIQUE KEY 防重复
```

---

### 交互6：OpenAPI接口文档生成

**日期：** 2026-05-18

**原始提示词：**
```
基于前后端分离原则，使用AI生成后端RESTful API接口文档模板（OpenAPI 3.0规范的YAML文件）。

要求：
1. 基础路径：/api
2. 认证方式：Bearer JWT
3. 统一响应格式：{ "code": 200, "message": "success", "data": {...} }
4. 分页响应格式：{ "items": [...], "total": 100, "page": 1, "page_size": 20 }
5. 包含以下模块：用户系统、内容系统、互动系统、社交系统、群组系统、发现搜索、行情数据、通知系统、管理系统

请先输出用户系统的接口定义作为样例。
```

**AI输出摘要：**
生成了OpenAPI 3.0.3规范的YAML文件，包含：
- 组件定义：ApiResponse, PaginatedResponse, ErrorResponse
- 各模块的Schema定义（RegisterRequest, LoginRequest, Post, Comment等）
- 路径定义及参数说明
- 响应状态码和错误格式

**可能存在的问题：**
1. AI生成的部分字段类型与Python模型不完全匹配（如int vs float）
2. 部分路径未覆盖完整CRUD
3. 枚举值定义与后端代码不一致

**迭代优化：**
```
V1.1修正：
- 统一所有数值类型为 int/float 与 Pydantic 模型匹配
- 补充：DELETE /comments/{id}、POST /comments/{id}/like 等缺失端点
- 修正：PostType 枚举值（normal/longtext/poll/realtime vs 原文 normal/long_article/poll）
- 增加：文件上传接口定义

V1.2补充：
- 补充管理后台全部接口（认证审核、敏感词CRUD、合规规则、行为监控等）
- 增加：404/409/422 等错误响应示例
- 优化：鉴权要求标注到每个路径上
```

---

### 交互7：前端UI设计

**日期：** 2026-05-18

**原始提示词：**
```
依据以下交互场景，使用AI生成前端页面设计。

场景：用户在论坛首页浏览板块列表，点击"股票讨论区"进入板块详情页，
翻到第2页查看帖子列表，点击帖子标题查看详情，然后点击"收藏"按钮收藏该帖子。

请描述以下内容：
1. 首页的页面布局（含导航、板块列表、内容区）
2. 板块详情页的帖子列表设计
3. 帖子详情页的布局（含评论区）
4. 收藏操作的交互反馈

请使用ASCII字符画出页面布局草图。
```

**AI输出摘要：**
- 首页布局：顶部导航+板块导航+左侧Feed流+右侧行情卡片
- 板块页：筛选栏+帖子列表（卡片式）+分页组件
- 帖子详情：标题区+作者信息+内容区+互动按钮区+评论区
- 收藏交互：点击收藏→按钮状态变化→Toast提示成功

**可能存在的问题：**
1. ASCII布局不够直观，难以转化为实际代码
2. 缺少移动端响应式设计考虑
3. 缺少管理后台的页面设计

**迭代优化：**
```
V1.1细化：
- 改用文字描述每个页面的组件树结构
- 增加：管理后台12个页面的布局设计
- 增加：响应式断点设计（sm/md/lg/xl）
- 增加：UI设计规范（色彩系统、间距、圆角）

V1.2补充：
- 增加：路由规划和导航守卫设计
- 增加：页面与组件映射表
- 增加：每个页面的数据来源API对应关系
```

---

## 模块3：AI辅助编码实现

### 交互8：代码生成 — 用户服务层

**日期：** 2026-05-22

**原始提示词：**
```
// 验证用户权限并返回JWT token

为FastAPI + SQLAlchemy项目实现用户注册功能。
要求：
1. 手机号查重
2. bcrypt密码哈希
3. 自动生成昵称（手机尾号）
4. 签发JWT Access Token + Refresh Token
5. Token Rotation机制
6. 返回用户Profile用于前端缓存

使用Python FastAPI + SQLAlchemy + PyJWT实现。
```

**AI输出摘要：**
生成了 `UserService.register()` 完整实现：
- 手机号查重 → 409异常
- `get_password_hash()` 使用 bcrypt
- 昵称自动生成逻辑
- `create_access_token()` + `create_refresh_token_record()`
- `_issue_token_pair()` 内部方法
- `_build_profile()` 构建用户资料

**可能存在的问题：**
1. Token过期时间硬编码 → 改为从配置读取
2. 缺少邮箱注册分支
3. 事务未处理异常回滚
4. 密码强度校验缺失

**迭代优化：**
```
V1.1修正：
- 过期时间改为从 settings 配置读取
- 增加：try-except 包裹 db.commit()，异常时 db.rollback()
- 增加：密码强度校验（≥8位，含字母+数字）
- 增加：邮箱注册对应方法 register_by_email()

提示词优化：
// 为用户注册方法增加事务回滚和密码强度校验
// 密码强度规则：至少8位，包含大小写字母和数字
// 事务要求：任何异常时回滚数据库操作
```

---

### 交互9：代码生成 — 敏感词检测服务

**日期：** 2026-05-25

**原始提示词：**
```
// 检查文本中是否包含敏感词，返回检测结果

为论坛内容审核系统实现敏感词检测服务。
要求：
1. 从数据库加载启用的敏感词列表
2. 三级检测：BLOCK（拦截）/ REVIEW（审核）/ WARN（警告）
3. 停用词不参与检测
4. 中文内容精确匹配
5. 返回命中的敏感词级别和详情

使用Python + SQLAlchemy实现。
```

**AI输出摘要：**
生成了 `SensitiveWordService` 完整实现：
- `check_content()` 方法，遍历敏感词库
- 三级返回：should_block / should_review / warn_only
- 停用词过滤（is_active=False）
- 中文精确匹配

**可能存在的问题：**
1. 逐条遍历敏感词效率低 → 建议增加缓存
2. 未处理英文大小写和全半角
3. 未处理部分匹配（如"发词"匹配到"禁发词"）

**迭代优化：**
```
V1.1优化：
- 增加：缓存敏感词列表（减少数据库查询）
- 增加：全半角归一化（ＮＦＫＣ）
- 增加：大小写归一化
- 增加：子串匹配优化（先检测是否包含再精确匹配）

提示词：
// 优化敏感词检测性能，增加缓存和文本归一化处理
// 要求：缓存活跃敏感词5分钟、NFKC归一化、全半角转换
```

---

### 交互10：代码生成 — 重复内容检测

**日期：** 2026-05-26

**原始提示词：**
```
// 检测用户发帖是否为重复内容

为论坛实现重复内容检测服务。
要求：
1. 检测当前用户最近50条帖子
2. 文本归一化（去标点/小写/NFKC）
3. 精确匹配 → 拦截
4. 模糊匹配（SequenceMatcher ≥ 92%）→ 审核
5. 短文本（<20字符）跳过检测

使用Python + difflib.SequenceMatcher实现。
```

**AI输出摘要：**
生成了 `DuplicateContentService` 完整实现：
- `_normalize_text()` 文本归一化
- `check_duplicate_post_content()` 检测逻辑
- `DuplicateContentCheckResult` 结果数据类
- 三种结果：exact_duplicate / near_duplicate / no_duplicate

**可能存在的问题：**
1. SequenceMatcher 在长文本时性能开销大
2. 只检测同一用户的内容，未检测跨用户重复
3. 92%阈值未经实际数据验证

**迭代优化：**
```
V1.1优化：
- 增加：先比较长度差异超过50%则跳过（性能优化）
- 增加：可配置的阈值参数
- 限制：匹配范围从全部帖子改为最近50条

提示词：
// 优化重复内容检测性能，增加长度过滤
// 如果现有文本长度与新文本相差超过50%，跳过相似度计算
```

---

### 交互11：AI辅助 Bug 定位

**日期：** 2026-06-10

**原始提示词：**
```
以下是我的FastAPI后端服务错误日志，请分析可能的原因和修复建议。

错误日志：
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: likes.user_id

触发操作：用户点赞帖子时触发
技术栈：FastAPI + SQLAlchemy + SQLite
```

**AI输出分析：**
- 根因：用户对同一帖子重复点击点赞，唯一约束冲突
- 修复方案：改为 INSERT ... ON CONFLICT DO NOTHING 或先查询再决定插入/删除
- 建议：实现点赞/取消点赞的 toggle 逻辑

**实际修复：**
```python
# 修改前：直接 INSERT 导致唯一约束冲突
like = Like(user_id=user_id, target_type="post", target_id=post_id)
db.add(like)

# 修改后：先查询，存在则删除（取消点赞），不存在则新建（点赞）
existing = db.query(Like).filter(
    Like.user_id == user_id,
    Like.target_type == "post",
    Like.target_id == post_id
).first()
if existing:
    db.delete(existing)
    liked = False
else:
    db.add(Like(user_id=user_id, target_type="post", target_id=post_id))
    liked = True
```

**经验总结：** 多态点赞设计需要先查后写，不能用简单的 INSERT。

---

### 交互12：代码重构

**日期：** 2026-06-12

**原始提示词：**
```
// 重构以下代码，使其更简洁、可维护

以下是我在FastAPI路由中写的用户资料更新逻辑，感觉太冗余：

```python
@router.put("/profile")
async def update_profile(data: dict, db: Session = Depends(get_db), 
                          current_user: User = Depends(get_current_user)):
    if "nickname" in data:
        current_user.nickname = data["nickname"]
    if "bio" in data:
        current_user.bio = data["bio"]
    if "avatar_url" in data:
        current_user.avatar_url = data["avatar_url"]
    if "tags" in data:
        current_user.tags = data["tags"]
    # ... 还有更多字段
    db.commit()
    return {"data": current_user}
```

请使用更Pythonic的方式重构。
```

**AI输出重构建议：**
```python
from sqlalchemy.orm import Session

UPDATABLE_FIELDS = {"nickname", "bio", "avatar_url", "tags", "favorite_markets", "risk_preference"}

@router.put("/profile")
async def update_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 仅更新传入的非空字段
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field in UPDATABLE_FIELDS & update_data.keys():
        setattr(current_user, field, update_data[field])
    db.commit()
    db.refresh(current_user)
    return {"data": current_user}
```

**优化效果：**
- 代码行数：20行 → 8行
- 新增字段无需修改代码，只需更新 `UPDATABLE_FIELDS` 集合
- 使用 Pydantic 的 `exclude_unset=True` 自动识别前端传入的字段

---

### 交互13：代码生成 — Token刷新与安全

**日期：** 2026-06-05

**原始提示词：**
```
// 实现JWT Token Rotation机制

为论坛的Token刷新实现安全加固：
1. 每次刷新时吊销旧Refresh Token
2. 检测到已吊销的Token尝试刷新 → 401并告警
3. Token哈希存储（不存明文）
4. 设置Token过期时间

要求：防止Token重放攻击。
```

**AI输出摘要：**
生成了 `refresh_token()` 完整方法：
- 查询RefreshToken记录（by hash）
- 检查 is_revoked 标志
- 检查 expires_at
- 吊销旧Token → 创建新Token对
- 检测已吊销Token的重试 → 可能为Token泄露，建议一并吊销该用户全部Token

**可能存在的问题：**
1. 缺少"Token族"吊销策略（一个Token被重用，同族全部吊销）
2. 未记录吊销原因

**迭代优化：**
```
V1.1增强：
- 增加：Token族吊销（检测到已吊销Token的重试时，吊销该用户全部RefreshToken）
- 增加：revoked_at 时间戳记录
- 增加：日志告警

提示词：
// 增强Token刷新安全：检测到已吊销Token的重试时，吊销该用户全部RefreshToken
// 这可能是Token泄露的迹象
```

---

### 交互14：代码生成 — 前端API调用

**日期：** 2026-06-08

**原始提示词：**
```
// 实现前端API调用拦截器，自动处理Token刷新

为Vue 3 + Axios项目实现：
1. 请求拦截器：自动附加JWT Token
2. 响应拦截器：检测401时自动尝试刷新Token
3. 刷新成功 → 重放原请求
4. 刷新失败 → 清除登录状态，跳转登录页
5. 防止并发刷新Token（多个请求同时401时只刷新一次）
```

**AI输出摘要：**
生成了完整的 Axios 拦截器配置：
- `axios.interceptors.request.use()` 自动附加 Authorization header
- `axios.interceptors.response.use()` 检测401
- 使用 Promise 队列防止并发刷新
- 使用 Pinia auth store 管理登录状态

**可能存在的问题：**
1. 刷新Token的请求本身也会被拦截器处理，导致死循环
2. 并发请求时多个401请求同时触发刷新

**迭代优化：**
```
V1.1修正：
- 增加：刷新Token的请求跳过拦截器（白名单）
- 增加：isRefreshing 标志位 + 等待队列
- 增加：最大重试次数限制

提示词：
// 修复Token刷新拦截器的并发问题
// 1. 刷新Token的请求不加Authorization header
// 2. 用isRefreshing+等待队列处理并发401
// 3. 限制最大重试次数为1次
```

---

### 交互15：代码解释 — 热度算法

**日期：** 2026-06-15

**原始提示词：**
```
请逐行解释以下热度计算代码的每一行作用：

```python
def calculate_heat_score(post):
    now = datetime.now(timezone.utc)
    age_hours = (now - post.created_at).total_seconds() / 3600
    base_score = (
        post.view_count * 1 +
        post.like_count * 5 +
        post.comment_count * 8 +
        post.collect_count * 4
    )
    if age_hours < 1:
        time_boost = 2.0
    elif age_hours < 24:
        time_boost = 1.0 + (24 - age_hours) / 24
    else:
        time_boost = max(0.1, 1.0 / age_hours)
    return round(base_score * time_boost, 2)
```
```

**AI输出解释：**
- 第1行：定义函数，接收帖子对象作为参数
- 第2行：获取当前UTC时间
- 第3行：计算帖子发布至今的小时数
- 第4-8行：基础分 = 阅读量×1 + 点赞量×5 + 评论量×8 + 收藏量×4（加权，评论权重最高）
- 第9-10行：1小时内发布的帖子获得2倍时间加成
- 第11-12行：24小时内按剩余时间线性衰减（24小时时无加成）
- 第13-14行：超过24小时按 1/age_hours 衰减，最低0.1倍
- 第15行：返回保留2位小数的热度分

**团队讨论结果：**
权重设置合理，但建议增加转发量的权重（+3）和分享量的权重（+2），因为分享表示用户主动传播。

---

### 交互16：异常处理 — 行情数据源降级

**日期：** 2026-06-18

**原始提示词：**
```
以下是我的行情数据获取代码的异常栈，请给出修复方案：

异常信息：
httpx.ConnectTimeout: timed out
URL: https://push2.eastmoney.com/api/qt/ulist.np/get
触发场景：用户访问首页行情卡片时
```

**AI输出分析：**
- 根因：东方财富API超时（可能网络限制或频率限制）
- 建议：实现多级降级策略
  - 第一级：东方财富（超时5秒）
  - 第二级：新浪财经（备用数据源）
  - 第三级：返回空数据标记

**实际修复：**
```python
async def get_indices():
    try:
        # 一级：东方财富
        data = await fetch_eastmoney(timeout=5.0)
        return parse_eastmoney(data)
    except (ConnectTimeout, HTTPStatusError):
        try:
            # 二级：新浪降级
            data = await fetch_sina(timeout=5.0)
            return parse_sina(data)
        except (ConnectTimeout, HTTPStatusError):
            # 三级：返回空数据
            return {"source": "none", "data": [], "message": "行情数据暂不可用"}
```

---

### 交互17：前端组件生成 — 评论组件

**日期：** 2026-06-08

**原始提示词：**
```
// 生成Vue 3评论组件，支持楼中楼回复

生成一个Vue 3评论列表组件，要求：
1. 显示评论列表（使用props传入）
2. 每条评论显示头像、昵称、时间、内容、点赞数
3. 支持楼中楼（parent_id），缩进显示
4. 点击"回复"按钮展开回复输入框
5. 支持@用户名回复
6. 使用Pinia管理评论数据
```

**AI输出摘要：**
生成了 `CommentList.vue` 和 `CommentItem.vue` 组件：
- CommentList：接收评论数组，按层级渲染
- CommentItem：递归渲染楼中楼（CommentItem嵌套自身）
- 回复输入框：点击"回复"显示/隐藏
- @提及：使用 MentionTextarea 子组件

**可能存在的问题：**
1. 递归组件需要在 Vue 3 中显式设置 name
2. 大量评论时递归渲染性能问题

**迭代优化：**
```
V1.1优化：
- 增加：CommentItem 组件显式设置 name: 'CommentItem'
- 限制：楼中楼最多支持2层（一级评论 → 回复 → 回复的回复全部平铺）
- 增加：懒加载（初次只加载一级评论，点击"展开回复"再加载楼中楼）

提示词：
// 优化评论组件的递归渲染
// 1. 显式设置组件name
// 2. 楼中楼限制2层深度
// 3. 使用v-if控制展开/折叠
```

---

### 交互18：管理后台 — 板块管理页面

**日期：** 2026-06-20

**原始提示词：**
```
// 生成管理后台板块管理页面的grid布局

板块管理页面需要：
1. 表头：排序、名称、类型、帖子数、状态、操作
2. 每行对应一个板块，顶级分区突出显示
3. 子板块在父分区下方缩进显示
4. 操作按钮：编辑、删除、添加子板块
5. 使用CSS Grid布局

要求：表头和数据列宽一致对齐。
```

**AI输出摘要：**
生成了 `admin/Categories.vue` 的CSS Grid布局：
```css
.cat-list__header, .cat-list__row {
    display: grid;
    grid-template-columns: 50px 1fr 70px 70px 70px max-content;
}
```

**可能存在的问题：**
`max-content` 导致每行列宽不一致（表头和每行是独立的grid容器）。修复为固定宽度 `180px` 确保对齐。

---

### 交互19：数据库迁移脚本

**日期：** 2026-06-22

**原始提示词：**
```
// 为板块表生成重排序的SQL脚本

需要在数据库中重新排序板块：
1. 顶级分区按sort_order排序
2. 每个分区下的子板块按sort_order排序
3. 排序号从1开始连续

生成Python脚本使用SQLite3实现。
```

**AI输出摘要：**
```python
import sqlite3
conn = sqlite3.connect('stock_fund_forum.db')
# 顶级分区按 sort_order 排序
sections = conn.execute(
    'SELECT id, name FROM categories WHERE parent_id IS NULL ORDER BY sort_order, id'
).fetchall()
for i, (sid, sname) in enumerate(sections):
    conn.execute('UPDATE categories SET sort_order=? WHERE id=?', (i+1, sid))
    # 子板块按 sort_order 排序
    children = conn.execute(
        'SELECT id, name FROM categories WHERE parent_id=? ORDER BY sort_order, id',
        (sid,)
    ).fetchall()
    for j, (cid, cname) in enumerate(children):
        conn.execute('UPDATE categories SET sort_order=? WHERE id=?', (j+1, cid))
conn.commit()
```

**验证查询：** 使用 LEFT JOIN 验证排序结果，检查父子关系是否正确。

---

## AI使用技巧总结

### 有效提示词模式

| 场景 | 有效模式 | 示例 |
|------|---------|------|
| 代码生成 | 注释开头 + 详细需求 | `// 实现JWT Token Rotation机制` |
| Bug定位 | 错误日志 + 触发操作 + 技术栈 | 粘贴完整异常栈 + 操作描述 |
| 代码重构 | 标注重构目标 + 原始代码 | `// 重构以下代码，使其更简洁` |
| 代码解释 | 逐行解释要求 | `请逐行解释以下代码的每一行作用` |
| 批量生成 | 明确格式 + 数量要求 | `每个功能至少生成2-3个用户故事` |

### 迭代优化策略

1. **分步细化**：不要一次给AI太多要求，先给核心需求，再逐步补充
2. **明确边界**：在提示词中说明"不需要"的内容，减少无关输出
3. **提供上下文**：粘贴相关代码片段，让AI理解现有逻辑
4. **验证输出**：AI生成的代码必须经过人工审查，特别是安全相关逻辑
5. **保留历史**：每次迭代保留提示词和输出记录，便于回溯

### 使用限制与注意事项

| 限制 | 应对策略 |
|------|---------|
| AI可能生成过时的API用法 | 指定版本号（如 `FastAPI 0.109+`） |
| AI可能忽略异常处理 | 提示词中明确要求 try-except |
| AI可能生成安全漏洞 | 安全相关代码必须人工审查 |
| AI输出可能过长 | 分批次提示，每次聚焦一个模块 |
| AI可能产生幻觉 | 验证关键逻辑，特别是数据库操作 |

# AI 使用文档

> **项目**：股票基金投资论坛（Stock-Fund-Investment-Forum）
> **记录周期**：2026-04-30 ~ 2026-06-17
> **AI 工具**：GitHub Copilot（模型：DeepSeek V4 Flash）+claude code（模型：DeepSeek V4 Flash）
> **覆盖阶段**：需求分析 → 系统设计 → 编码实现 → 测试调试
>由于md文件图片传输较为复杂，故相关图片仅在报告相应位置展示
---

## 一、AI 辅助需求分析

### 交互1：生成用户故事

**日期：** 2026-05-06｜**对应文档：** `docs/user_stories.md`

**原始提示词：**
```
作为产品经理，为【股票基金投资论坛】生成用户故事。
功能包括：用户注册登录、帖子发布与管理、评论互动、社交关系、群组社区、搜索发现、行情数据、通知消息、管理后台。
格式：作为一名…我想…以便...。每个功能至少2-3个，覆盖访客、注册用户、管理员三种角色。
```

**AI输出摘要：**
生成 16 条初始用户故事，覆盖 5 大模块（用户系统、内容系统、社交系统、信息整合系统、管理运营系统），每条按照"作为一名…我想…以便…"格式输出，包含角色-操作-价值三段式描述。

**可能存在的问题：**
1. 缺少专业认证、风险评估等金融合规场景
2. 积分等级等用户激励体系未覆盖
3. 缺少隐私控制和内容合规需求
4. 用户角色只有3种，无法区分普通用户和专业用户

**迭代优化：**
```
V1.1补充5个遗漏场景：专业认证、风险评估、积分等级、隐私控制、内容合规
V1.1用户角色从3种扩展到6种（增加：认证用户、持牌分析师、群主）
V1.2每条故事补充验收标准（Acceptance Criteria）
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 用户角色 | 3种（访客/用户/管理员） | 6种（+认证用户/分析师/群主） | 金融社区需区分专业用户 |
| V1→V2 | 认证体系 | 仅基础注册登录 | 增加专业认证、风险评估流程 | 满足监管合规要求 |
| V1→V2 | 积分等级 | 未涉及 | 增加积分获取途径和等级晋升机制 | 用户激励体系缺失 |
| V1→V2 | 隐私控制 | 未涉及 | 增加隐私设置选项 | 用户数据保护需求 |
| V1→V2 | 内容合规 | 未涉及 | 增加敏感词检测、重复内容检测 | 金融社区内容审核刚需 |
| V2→V3 | 验收标准 | 仅有故事描述 | 每条补充Acceptance Criteria | 便于开发理解需求边界 |

---

### 交互2：生成交互场景

**日期：** 2026-05-10｜**对应文档：** `docs/use_cases.md`

**原始提示词：**
```
为【股票基金投资论坛】书写交互场景 — US-01 手机号注册。
要求格式：用例名称、对应故事、参与者、前置条件、后置条件、基本流程、备选路径。
包含正常流程和至少3个异常流程（验证码错误、手机号已注册、密码强度不足）。
```

**AI输出摘要：**
生成 14 个完整用例，覆盖以下场景：手机号注册、实名认证、用户发帖、投票调查、评论回复、点赞收藏转发、关注用户、创建群组、个性化推荐、热榜排行、搜索股票、内容审核、举报违规、数据统计。每个用例包含主流程和异常分支。

**可能存在的问题：**
1. 异常流程覆盖不足，每个用例仅1-2个异常分支
2. 缺少外部系统交互描述（短信服务、人脸识别等）
3. 部分用例缺少前置条件和后置条件
4. 并发场景未考虑（同时点赞、重复提交等）

**迭代优化：**
```
V1.1：每个用例补充至3-5个异常分支（网络超时、输入错误、权限不足等）
V1.1：补充副参与者和外部系统（短信服务、人脸识别SDK等）
V1.2：全部补全前置条件和后置条件
V1.2：增加并发操作场景（同时点赞、重复提交等）
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 异常流程 | 每个仅1-2个 | 补充至3-5个 | 测试需更多边界覆盖 |
| V1→V2 | 参与者 | 仅主参与者 | 补充短信服务、人脸SDK等 | 明确系统间依赖 |
| V2→V3 | 前置/后置条件 | 部分缺失 | 全部补全 | 完整描述场景上下文 |
| V2→V3 | 并发场景 | 未考虑 | 增加并发操作场景 | 真实生产环境常见 |

---

### 交互3：细化积分等级体系

**日期：** 2026-05-08｜**对应代码：** `backend/app/services/points_service.py`

**原始提示词：**
```
对于【股票基金投资论坛】，如何理解积分等级体系？
1. 积分的获取途径有哪些？
2. 等级如何计算和晋升？
3. 积分和等级对用户有什么实际价值？
4. 需要考虑哪些防作弊机制？
```

**AI输出摘要：**
推荐 8 级等级体系（阈值：100/300/600/1000/2000/5000/10000），发帖奖励 +3 积分，评论奖励 +1 积分，每日签到 +2 积分，防作弊机制包括签到频率限制、异常行为检测和告警。

**可能存在的问题：**
1. 发帖和评论奖励偏低，激励效果不足
2. 缺少每日积分获取上限，容易被刷分
3. 等级名称通用（Lv1~Lv8），缺少社区特色
4. 代码实现缺少 `PointsHistory` 模型定义

**迭代优化：**
```
V1.1：发帖奖励从+3调至+5，评论奖励从+1调至+2
V1.1：增加每日积分获取上限100分
V1.1：等级名称改为金融社区风格（新手→学徒→分析师→专家→股神）
V1.2：补充PointsHistory模型和get_level()函数实现
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 发帖奖励 | +3 积分 | +5 积分 | 提高发帖积极性 |
| V1→V2 | 评论奖励 | +1 积分 | +2 积分 | 鼓励互动讨论 |
| V1→V2 | 每日上限 | 未设置 | 每日上限100分 | 防止刷分滥用 |
| V1→V2 | 等级名称 | Lv1~Lv8 | 自定义金融风格名称 | 增强社区归属感 |

---

## 二、AI 辅助系统设计

### 交互4：架构设计与技术选型

**日期：** 2026-05-16

**原始提示词：**
```
为一个股票基金投资论坛进行技术选型：
前后端分离、JWT认证、帖子发布（普通/投票/长文）、评论（楼中楼）、社交关系、群组社区、
实时行情数据、管理后台、敏感词检测和内容审核。请推荐技术栈并说明理由。
```

**AI输出摘要：**
推荐 Vue 3 + FastAPI + PostgreSQL + Celery + JWT Refresh Token Rotation 方案，前后端分离架构，RESTful API 设计。

**可能存在的问题：**
1. PostgreSQL 团队不熟悉，学习成本高
2. Celery + Redis 对于项目规模过于冗余
3. 行情数据单数据源存在单点故障风险
4. 文件上传缺少安全限制

**迭代优化：**
```
V1.1：数据库改为 MySQL 8.0（团队更熟悉）
V1.1：取消 Celery，改用同步+超时
V1.1：行情数据三级降级策略（东方财富→新浪→空数据）
V1.1：文件上传增加MIME白名单+10MB大小限制+病毒扫描
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI推荐） | 修改后（人工决策） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 数据库 | PostgreSQL | MySQL 8.0 | 团队更熟悉，减少学习成本 |
| V1→V2 | 异步任务 | Celery + Redis | 取消，改用同步+超时 | 项目规模小，无需消息队列 |
| V1→V2 | 行情数据源 | 单数据源 | 三级降级策略 | 行情API不稳定需容错 |
| V1→V2 | 文件上传 | 基础实现 | MIME白名单+10MB+病毒扫描 | 安全合规要求 |

---

### 交互5：数据库设计

**日期：** 2026-05-18｜**对应文件：** `database/schema.sql`

**原始提示词：**
```
根据需求提取类及其属性，生成数据库ER图（Mermaid格式）。
需求：用户注册、帖子发布、评论（楼中楼）、点赞、关注、群组、私信、板块树形结构、投票、管理后台。
标注主键和外键。
```

**AI输出摘要：**
生成 15 个核心实体（User、Post、Comment、Category、Like、Follow、Group、GroupMember、Message、Vote、VoteOption、Notification等），Comment 自引用实现楼中楼，Category 自引用实现树形结构。

**可能存在的问题：**
1. 未包含积分历史、敏感词、合规规则等运营表
2. 缺少全文索引设计，无法支持中文搜索
3. 删除策略未明确（软删除 vs 硬删除）
4. 点赞表缺少联合 UNIQUE KEY 可能导致重复数据

**迭代优化：**
```
V1.1：增加points_history、sensitive_words、compliance_rules、professional_certifications
V1.1：posts表增加FULLTEXT INDEX（title, content）
V1.1：采用状态字段（published/review/banned）代替物理删除
V1.2：增加privacy_settings JSON字段到users表
V1.2：notifications独立表（10种通知类型）
V1.2：所有点赞/关注表增加UNIQUE KEY约束
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 积分历史 | 未涉及 | 新增 points_history 表 | 积分变动需可追溯 |
| V1→V2 | 敏感词库 | 未涉及 | 新增 sensitive_words 表 | 内容审核需要 |
| V1→V2 | 合规规则 | 未涉及 | 新增 compliance_rules 表 | 监管合规需求 |
| V1→V2 | 全文索引 | 未涉及 | 增加 FULLTEXT INDEX | 支持中文全文搜索 |
| V1→V2 | 专业认证 | 未涉及 | 新增 professional_certifications 表 | 分析师认证流程 |
| V2→V3 | 隐私设置 | 固定字段 | 改为 JSON flexible schema | 便于前端扩展 |
| V2→V3 | 通知 | 字段内嵌 | 独立 notifications 表 | 需独立管理和查询 |
| V2→V3 | 唯一约束 | 缺少 | 补充联合 UNIQUE KEY | 防止数据重复 |

**最终成果：** 33 张数据库表，MySQL 8.0。

---

### 交互6：OpenAPI 接口文档

**日期：** 2026-05-18｜**对应文件：** `openapi.yaml`

**原始提示词：**
```
生成OpenAPI 3.0 YAML模板。基础路径/api，Bearer JWT认证。
统一响应{code,message,data}，分页响应{items,total,page,page_size}。
模块：用户、内容、互动、社交、群组、发现、行情、通知、管理。
先输出用户系统作为样例。
```

**AI输出摘要：**
生成 OpenAPI 3.0.3 规范 YAML，包含组件定义（ApiResponse、PaginatedResponse、ErrorResponse）、各模块 Schema（RegisterRequest、LoginRequest、Post、Comment 等）、路径定义及参数说明、响应状态码和错误格式。

**可能存在的问题：**
1. 字段类型与 Pydantic 模型不匹配（int vs float）
2. 部分路径未覆盖完整 CRUD（缺少 DELETE 等）
3. 枚举值定义与后端代码不一致
4. 缺少管理后台接口定义
5. 缺少错误响应示例

**迭代优化：**
```
V1.1：逐项对齐 int/float 字段类型
V1.1：补充 DELETE /comments/{id}、POST /comments/{id}/like 等缺失端点
V1.1：统一 PostType 枚举值
V1.2：补充管理后台全部接口（认证审核、敏感词CRUD、合规规则）
V1.2：增加404/409/422等错误响应示例
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 字段类型 | 部分与Pydantic不匹配 | 逐项对齐 int/float/string | FastAPI校验会报错 |
| V1→V2 | CRUD覆盖 | 缺少DELETE路径 | 补充 DELETE /comments/{id} 等 | RESTful要求完整CRUD |
| V1→V2 | 枚举值 | 与后端不一致 | 统一 PostType 等枚举定义 | 前后端不一致联调失败 |
| V2→V3 | 管理接口 | 未覆盖 | 补充审核/敏感词/合规CRUD | 管理后台需要对应API |
| V2→V3 | 错误示例 | 缺少 | 补充 404/409/422 响应示例 | 前端需要对错误做处理 |

---

### 交互7：前端 UI 设计与路由规划

**日期：** 2026-05-18

**原始提示词：**
```
依据交互场景描述前端页面设计：
场景：用户在论坛首页浏览板块列表，点击"股票讨论区"进入板块详情页，
翻到第2页查看帖子列表，点击帖子标题查看详情，然后点击"收藏"按钮收藏该帖子。
描述首页布局、板块页帖子列表、帖子详情页布局（含评论区）、收藏操作交互反馈。
使用ASCII字符画出页面布局草图。
```

**AI输出摘要：**
首页布局（顶部导航+板块导航+左侧Feed流+右侧行情卡片），板块页（筛选栏+帖子卡片列表+分页组件），帖子详情页（标题区+作者信息+内容区+互动按钮+评论区），收藏交互（点击→按钮状态变化→Toast提示成功）。

**可能存在的问题：**
1. ASCII 布局不够直观，难以转化为代码
2. 缺少移动端响应式设计
3. 缺少管理后台的页面设计
4. 缺少路由规划和导航守卫

**迭代优化：**
```
V1.1：ASCII布局改为文字描述组件树结构
V1.1：补充12个管理后台页面布局
V1.1：补充响应式断点设计（sm/md/lg/xl）
V1.1：补充UI设计规范（色彩系统、间距、圆角）
V1.2：增加路由规划和导航守卫设计
V1.2：增加页面与组件映射表
V1.2：增加每个页面的数据来源API对应关系
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 布局形式 | ASCII 草图 | 文字描述组件树结构 | ASCII图无法直接开发 |
| V1→V2 | 管理后台 | 未涉及 | 补充12个管理后台页面布局 | 管理后台是项目组成部分 |
| V1→V2 | 响应式 | 固定宽度设计 | 增加 sm/md/lg/xl 断点 | 用户多设备访问 |
| V2→V3 | 路由守卫 | 未涉及 | 增加导航守卫 | 保护需要认证的路由 |

---

## 三、AI 辅助编码实现

### 交互8：用户注册服务 — bcrypt + JWT

**日期：** 2026-05-22｜**对应文件：** `backend/app/services/user_service.py`

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
- `_hash_password()` 使用 bcrypt
- 昵称自动生成逻辑 `用户{尾号}`
- `_create_access_token()` + `_create_refresh_token_record()`
- `_issue_token_pair()` 内部方法
- `_build_profile()` 构建用户资料

**可能存在的问题：**
1. Token过期时间硬编码 → 配置文件环境不同策略不同
2. 缺少邮箱注册分支 → 仅支持手机号
3. 事务未处理异常回滚 → 异常时产生脏数据
4. 密码强度校验缺失 → 弱密码安全隐患

**迭代优化：**
```
V1.1修正：
- 过期时间改为从 settings 配置读取
- 增加：try-except 包裹 db.commit()，异常时 db.rollback()
- 增加：密码强度校验（≥8位，含字母+数字）
- 增加：邮箱注册对应方法 register_by_email()

V1.2修正：
- 昵称生成增加随机后缀，防止同名冲突
- _build_profile() 排除 password_hash 等敏感字段
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | Token过期时间 | 硬编码30分钟 | settings配置读取 | 开发/生产环境超时不同 |
| V1→V2 | 事务处理 | 无异常处理 | try-except + rollback | 避免脏数据 |
| V1→V2 | 密码强度 | 无校验 | ≥8位含字母+数字 | 弱密码安全隐患 |
| V1→V2 | 注册方式 | 仅手机号 | 增加 register_by_email() | 产品需求 |
| V2→V3 | 昵称策略 | 仅手机尾号 | 增加随机后缀防重名 | 同名冲突 |
| V2→V3 | 返回字段 | 含password_hash | 排除敏感字段 | 安全规范 |

---

### 交互9：敏感词检测服务

**日期：** 2026-05-25｜**对应文件：** `backend/app/services/sensitive_word_service.py`

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
- 增加：缓存敏感词列表（5分钟过期）
- 增加：全半角归一化（NFKC）
- 增加：大小写归一化

提示词优化：
// 优化敏感词检测性能，增加缓存和文本归一化处理
// 要求：缓存活跃敏感词5分钟、NFKC归一化、全半角转换
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 遍历方式 | 逐条DB查询 | 缓存5分钟减少DB查询 | 性能优化 |
| V1→V2 | 全半角 | 未处理 | 增加NFKC归一化 | 全半角不同导致漏检 |
| V1→V2 | 大小写 | 未处理 | 增加大小写归一化 | 英文大小写不匹配 |

---

### 交互10：重复内容检测服务

**日期：** 2026-05-26｜**对应文件：** `backend/app/services/duplicate_content_service.py`

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
- 增加：可配置的阈值参数 NEAR_DUPLICATE_THRESHOLD
- 限制：匹配范围从全部帖子改为最近50条

提示词优化：
// 优化重复内容检测性能，增加长度过滤
// 如果现有文本长度与新文本相差超过50%，跳过相似度计算
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 性能优化 | 无长度过滤 | 长度差异>50%跳过计算 | 减少不必要的计算 |
| V1→V2 | 阈值 | 硬编码92% | 可配置参数 | 环境不同需调整 |
| V1→V2 | 匹配范围 | 全部帖子 | 限最近50条 | 提高效率 |

---

### 交互11：隐私设置 — Pydantic 部分更新

**日期：** 2026-06-05｜**对应文件：** `backend/app/api/auth.py`

**原始提示词：**
```
重构隐私设置更新逻辑，使其更简洁。
支持前端只传需要修改的字段，未传字段保持原值。
使用Python FastAPI + Pydantic实现。
```

**AI输出摘要：**
使用 `model_dump(exclude_unset=True)` 实现部分更新。AI 建议的代码：
```python
stored = current_user.privacy_settings or {}
update_data = data.model_dump(exclude_unset=True)
stored.update(update_data)
current_user.privacy_settings = stored
db.commit()
```

**可能存在的问题：**
1. AI 使用 `data.dict()` 而非 `data.model_dump()`（Pydantic v2）
2. 未处理 JSON 字段为 None 的情况

**迭代优化：**
```
V1.1：使用 model_dump() 替代已废弃的 dict()
V1.1：增加 stored = {} 的默认值处理
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 更新方式 | 全量覆盖 `data.dict()` | 部分更新 `model_dump(exclude_unset=True)` | 前端只传修改字段 |
| V1→V2 | None处理 | 未处理 | 增加 `{}` 默认值 | 首次未设置时为None |

---

### 交互12：JWT Token 认证体系搭建 + 数据库自动初始化

**日期：** 2026-06-09｜**对应文件：** `backend/app/core/config.py`、`backend/app/core/security.py`、`backend/app/core/dependencies.py`、`backend/app/main.py`、`backend/.env`

**原始提示词：**
```
阅读项目中的各项定义文档，了解项目的预期功能和详细后端API标准，严格遵循规定的技术和安全标准。
我是负责后端的，帮我检查JWT Token鉴定。

DATABASE=stock_fund_forum9 JWT_SECRET=dev-jwt-secret-change-in-production-a7f3c9e JWT_ALGORITHM=HS256
```

**AI输出摘要：**

| 组件 | 文件 | 功能 |
|:----:|------|------|
| Settings | `config.py` | 从环境变量读取 `jwt_secret`、`jwt_algorithm`、`database_url` |
| JWT 工具 | `security.py` | `create_access_token()` + `decode_access_token()`，含 exp/iat/type 声明 |
| 密码工具 | `security.py` | `get_password_hash()` (bcrypt cost=12) + `verify_password()` |
| 依赖注入 | `dependencies.py` | `get_current_user()` 解析 Bearer Token → 返回 User 对象 |
| 限流器 | `dependencies.py` | `RateLimiter`（IP 维度）+ `UserRateLimiter`（用户维度） |
| 启动初始化 | `main.py` | `lifespan` 自动建表 + 种子数据（管理员/板块/演示内容） |

**主要修改 — main.py 启动生命周期改造：**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (dev convenience — use migrations in production)."""
    Base.metadata.create_all(bind=engine)   # 自动建表
    seed_admin()                             # 初始化管理员
    seed_categories()                        # 初始化板块
    seed_demo_content()                      # 初始化演示数据
    yield
```

同时确保所有模型在 `create_all` 前被导入注册：
```python
import app.models.user           # noqa: F401
import app.models.refresh_token  # noqa: F401
import app.models.certification   # noqa: F401
...
```

**可能存在的问题：**
1. `create_all` 仅适用于开发环境，生产环境应使用 Alembic 迁移
2. 种子数据中的管理员密码来自环境变量，首次部署需设置
3. 板块种子数据固定，生产环境应通过管理后台动态管理

**迭代优化：**
```
V1.1：config.py 增加 jwt_secret/jwt_algorithm 从环境变量读取
V1.1：main.py 增加 lifespan 生命周期 + 模型导入
V1.1：dependencies.py 增加 get_current_user 依赖
V1.1：security.py 统一 JWT 创建/验证/密码哈希
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前 | 修改后 | 修改原因 |
|:----:|--------|-------|-------|---------|
| V1→V2 | JWT Secret | 硬编码 `"your-jwt-secret-key-change-in-production"` | 从 `JWT_SECRET` 环境变量读取 | 敏感信息不应硬编码 |
| V1→V2 | 数据库建表 | 手动执行 schema.sql | `lifespan` 自动 `create_all` | 开发环境便利性 |
| V1→V2 | 模型注册 | 部分模型未导入 | 全部 import models.* (noqa: F401) | 确保 metadata 完整 |
| V1→V2 | 种子数据 | 无 | 自动创建管理员+板块+演示帖子 | 开发环境快速启动 |

---

### 交互13：邮箱注册机制 — 后端 SMTP 验证码 + 前端邮箱注册页

**日期：** 2026-06-12｜**对应文件：** `backend/app/services/email_service.py`、`backend/app/api/auth.py`、`backend/.env`、`frontend/src/views/RegisterEmail.vue`、`frontend/src/views/Register.vue`、`frontend/src/router/index.js`

**原始提示词：**
```
阅读项目文档，理解项目功能目标、开发路线和接口标准，检查项目文件，了解项目结构。
尽可能避免对标准的更改，若不得不更改则必须按照一致的标准更新相应定义文档。

现在向项目后端引入邮箱注册机制，使用服务器固定的SMTP邮箱向用户注册使用的邮箱发送
固定格式的验证码邮件，并验证该验证码正确后允许用户继续注册。
注意发送验证码用的SMTP邮箱、授权码等均应在.env进行本地设置以避免隐私信息泄露。

之后，在前端引入风格、排版和各项标准与手机注册页面一致的邮箱认证页面，
并在默认的手机号注册页面合适位置添加用于邮箱登录的重定向（同理，以及反向的重定向）。
```

**AI输出摘要：**

**后端实现：**
| 组件 | 文件 | 说明 |
|:----:|------|------|
| EmailService | `email_service.py` | SMTP 发送验证码，含 console fallback（开发模式） |
| SMTP 配置 | `.env` | `SMTP_HOST/PORT/USER/PASSWORD/FROM_EMAIL` |
| 限流器 | `auth.py` | `email_register_limiter`（5次/60秒） |
| API 端点 | `auth.py` | `POST /auth/email/send-code`、`/auth/email/verify-code`、`/auth/email/register` |

SMTP 配置通过 `settings.smtp_configured` 检测，未配置时自动降级为控制台打印验证码，方便开发调试。

**前端实现：**
| 页面 | 路由 | 说明 |
|------|:----:|------|
| `RegisterEmail.vue` | `/register/email` | 三步流程：邮箱验证→设置密码→完善资料 |
| `Register.vue` | `/register` | 手机号注册页，底部增加"使用邮箱注册"链接 |

页面风格与手机注册完全一致（`auth-card`、`auth-page` 样式复用）。
双向重定向：手机注册页 → "使用邮箱注册" → `/register/email`；邮箱注册页 → "使用手机注册" → `/register`。

**可能存在的问题：**
1. SMTP 发送是阻塞操作，直接调用会阻塞 FastAPI 事件循环
2. 开发模式下验证码直接打印在控制台，前端无法获取

**迭代优化：**
```
V1.1：SMTP发送改为 asyncio.to_thread + timeout，避免阻塞事件循环
V1.1：开发模式下 API 返回 dev_code 字段，前端通过 Toast 展示
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前 | 修改后 | 修改原因 |
|:----:|--------|-------|-------|---------|
| V1→V2 | SMTP 调用 | 直接同步调用 | `asyncio.to_thread(EmailService._send_smtp, ...)` + 超时 | 避免阻塞 FastAPI 异步事件循环 |
| V1→V2 | 开发验证码 | 仅打印控制台 | API 返回 `dev_code`，前端 Toast 展示 | 开发时无法查看控制台，调试不便 |

---

### 交互14：管理运营系统前端 — 重复内容检测 + 行为监控

**日期：** 2026-06-13｜**对应文件：** `frontend/src/views/admin/DuplicateContent.vue`、`frontend/src/views/admin/BehaviorMonitor.vue`、`frontend/src/views/admin/ActivityLogs.vue`、`frontend/src/api/admin.js`、`frontend/src/router/index.js`

**原始提示词：**
```
现在项目中缺少功能：
内容审核-重复内容检测后端已实现但前端无展示；
用户行为监控（发帖频率/内容质量）后端有ActivityLog但前端无行为监控展示页面；
二者皆从属于管理运营系统。
依次实现二者对应的前端，注意若需创建新界面，则前端页面风格和排版逻辑应合理且与当前已有界面保持一致。
```

**AI输出摘要：**
分析后端已有的 API 和前端已有的管理后台页面风格后，新建了 2 个管理页面：

**页面一：重复内容检测** (`/admin/duplicate-content`)
| Tab | 功能 | 说明 |
|:---:|------|------|
| 文本扫描 | 输入文本+时间范围，扫描重复 | 调用 `POST /admin/duplicate-content/scan` |
| 统计概览 | 展示重复统计数据 | 调用 `GET /admin/duplicate-content/stats` |

- `scanDuplicateContent()` 调用后端扫描接口
- `fetchDuplicateContentStats()` 加载统计数据
- 相似度显示使用 `similarityBadgeClass()` 区分精确匹配(≥0.99)/高相似(≥0.95)/中等(≥0.92)

**页面二：行为监控** (`/admin/behavior`)
| Tab | 功能 | API |
|:---:|------|-----|
| 操作日志 | 活动日志列表，可筛选类型/时间 | `GET /admin/activity-logs` |
| 用户行为汇总 | 用户行为统计数据，可排序 | `GET /admin/behavior/user-summary` |
| 可疑行为 | 可疑用户列表 | `GET /admin/behavior/suspicious` |

- 支持用户时间线弹窗查看（`showTimeline` 模态框）
- 活动类型中文映射（`activityLabelMap`）
- 筛选器：用户关键词、活动类型、日期范围

**可能存在的问题：**
1. 重复内容检测的文本扫描和统计概览放在同一个页面，Tab 切换可能导致状态混乱
2. 行为监控页面同时包含操作日志、用户汇总、可疑行为，数据量较大时加载性能需优化

**迭代优化：**
```
V1.1：DuplicateContent 拆分为 scan/stats 两个 Tab，各自独立加载
V1.1：BehaviorMonitor 增加筛选器和分页组件，避免一次性加载过多数据
V1.2：ActivityLogs 作为独立页面保留，BehaviorMonitor 中通过 Tab 包含日志查看
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前 | 修改后 | 修改原因 |
|:----:|--------|-------|-------|---------|
| V1→V2 | 重复内容页 | 单个视图 | scan/stats 双 Tab | 扫描和统计功能不同，分开更清晰 |
| V1→V2 | 行为监控页 | 无筛选 | 增加类型/时间筛选器 | 日志量大时需要筛选 |
| V1→V2 | 活动日志路由 | 仅 BehaviorMonitor 内嵌 | 独立 `/admin/logs` + BehaviorMonitor Tab | 两种访问方式，方便快捷查看 |

---

### 交互15：找回密码全流程 — 后端验证码校验 + 前端重置页面

**日期：** 2026-06-13｜**对应文件：** `backend/app/schemas/user.py`、`backend/app/services/user_service.py`、`backend/app/api/auth.py`、`frontend/src/api/auth.js`、`frontend/src/views/ForgotPassword.vue`、`frontend/src/views/Register.vue`、`frontend/src/views/Login.vue`、`frontend/src/router/index.js`

**原始提示词：**
```
注册方面的验证码，不能随便一个验证码都能通过
实现忘记密码时的验证码交互过程
```

**AI输出摘要：**
- 生成了 `VerifyCodeRequest` 和 `ResetPasswordRequest` 两个 Pydantic Schema
- 生成了 `verify_code()` 和 `reset_password()` 两个 Service 方法
- 生成了 `/auth/verify-code` 和 `/auth/reset-password` 两个 API 端点
- 生成了前端 `verifyCode()` 和 `resetPassword()` API 函数
- 生成了 `ForgotPassword.vue` 三步交互页面（step 1→2→3）
- 生成了路由配置

**可能存在的问题：**
1. AI 生成的 `ResetPasswordRequest` 中密码字段命名为 `new_password`，而前端已有逻辑使用 `password`，命名不一致
2. AI 初始生成的注册页面验证码校验逻辑缺少 loading 状态反馈
3. 重置密码成功后应自动跳转登录页，AI 初始版本缺少跳转逻辑

**迭代优化：**
```
V1.1：ResetPasswordRequest 密码字段改为 password（与前端保持一致）
V1.1：Register.vue submit 按钮增加 loading 状态
V1.1：ForgotPassword.vue Step 3 增加"去登录"按钮和自动跳转
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | Schema字段名 | `new_password: str` | `password: str` | 与前端现有逻辑保持一致 |
| V1→V2 | 注册loading | 无loading状态 | submit时显示loading | 防止用户重复点击 |
| V1→V2 | 成功跳转 | 仅显示成功提示 | 增加"去登录"按钮+3秒自动跳转 | 提升用户体验 |


---

### 交互16：管理后台板块列表 Grid 对齐修复

**日期：** 2026-06-14｜**对应文件：** `frontend/src/views/admin/Categories.vue`

**原始提示词：**
```
类型、帖子数这些展示的距离不用这么远但也不能那么近，正常一点

帖子数，类型这些跟下面真实数据应对齐

```

**AI输出摘要：**
逐轮调整板块管理页面的 Grid 布局：

| 轮次 | 修改内容 | 问题 |
|:----:|---------|------|
| V1 | 名称列可伸缩，类型/帖子数/状态固定70px靠右，操作列自适应，gap:12px | 间距过紧 |
| V2 | 名称列 1fr，操作列 max-content，gap: 16px | 子板块整行 padding-left 导致与表头错位 |
| V3 | 去掉 cat-list__row--child 的 padding-left，子板块缩进改由名称列内的 `<span class="cat-indent" />` 控制 | ✅ 各列对齐 |

**可能存在的问题：**
1. 间距从 12px 改为 16px 后需确认按钮区是否有足够空间
2. 操作列使用 `max-content` 在按钮较多时列宽可能波动

**迭代优化：**
```
V1.1：gap: 12px → 16px
V1.2：操作列 180px → max-content
V1.3：cat-list__row--child 去掉 padding-left，子板块缩进改由 cat-indent 控制
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前 | 修改后 | 修改原因 |
|:----:|--------|-------|-------|---------|
| V1→V2 | grid 间距 | `gap: 12px` | `gap: 16px` | 12px 太挤 |
| V1→V2 | 操作列 | 固定宽度 | `max-content` | 自适应按钮宽度 |
| V2→V3 | 子板块缩进 | 整行 `padding-left` | 名称列内 `<span class="cat-indent" />` | 整行 padding 导致与表头错位 |

---

### 交互17：页面导航空白 Bug 修复 — Transition 碎片根节点

**日期：** 2026-06-14｜**对应文件：** `frontend/src/App.vue`

**原始提示词：**
```
解决前端导航后页面变空白的问题
```

**AI输出摘要：**
定位到根因：`App.vue` 中 `<transition mode="out-in">` 直接包裹 `<component :is="Component">`。但大部分页面组件（Home、Category 等）是 **Fragment（多根节点）** — 模板中多个并列的 `<template v-if>/<template v-else>` 块。

Vue 3 的 `<Transition mode="out-in">` 要求先等旧页面完全离开、再让新页面进入。当组件是 Fragment 时，`transitionend` 事件可能无法正常触发，导致旧页面离开了、新页面一直卡在 `opacity: 0`，整个内容区变空白。

**修复方案：** 在 `<component>` 外层增加一个 `<div>` 包装，保证 transition 作用在单个根元素上：

```vue
<router-view v-slot="{ Component, route: resolvedRoute }">
  <transition name="page" mode="out-in" appear>
    <div :key="resolvedRoute.path" class="route-page-wrapper">
      <component :is="Component" />
    </div>
  </transition>
</router-view>
```

**可能存在的问题：**
1. 包装用的 `<div>` 可能影响页面布局排版
2. 不同页面的 wrapper 高度不一致可能导致 transition 动画抖动

**迭代优化：**
```
V1.1：wrapper 增加 class="route-page-wrapper"，通过 CSS 控制不影响布局
V1.1：key 绑定 resolvedRoute.path 确保路由变化时正确触发 transition
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前 | 修改后 | 修改原因 |
|:----:|--------|-------|-------|---------|
| V1→V2 | 组件包装 | 直接 `<component :is="Component">` | `<div class="route-page-wrapper"><component .../></div>` | Fragment 多根节点导致 transitionend 无法触发 |
| V1→V2 | transition key | 无 key | `:key="resolvedRoute.path"` | 确保路由切换时正确卸载/挂载组件 |

---

### 交互18：导航栏点击刷新问题修复 — SideBar 链接改造

**日期：** 2026-06-15｜**对应文件：** `frontend/src/components/common/SideBar.vue`

**原始提示词：**
```
解决一下每点击一次导航栏里的某一项页面都要刷新一次的问题
```

**AI输出摘要：**
定位到根因：`SideBar.vue` 中所有导航链接使用了 `<a href="javascript:void(0)" @click="navigate(item)">` 这种过时的反模式。

问题分析：
1. `href="javascript:void(0)"` 依赖 `javascript:` 伪协议阻止浏览器导航，但现代浏览器的 Content Security Policy 可能拦截这类 URL，导致浏览器执行实际的页面跳转（全页刷新）
2. `@click` 缺少 `.prevent` 修饰符，完全依赖 `javascript:void(0)` 阻止默认行为，不够健壮

**修复方案：** 将所有 `<a href="javascript:void(0)" @click="navigate(item)">` 替换为 Vue Router 的 `<router-link :to="...">` 组件。

**可能存在的问题：**
1. 移动端菜单自动关闭功能（`onNavClick()`）需要保留
2. `<router-link>` 默认渲染为 `<a>` 标签，需确保原有 CSS 样式不受影响

**迭代优化：**
```
V1.1：去掉 @click="navigate(item)"，改用 @click="onNavClick()" 保留关闭移动端菜单功能
V1.1：论坛板块使用 :to="`/categories/${child.id}`"
V1.1：发现和个人使用 :to="{ path: item.to, query: item.query }"
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（原代码） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 导航方式 | `<a href="javascript:void(0)">` | `<router-link :to="...">` | CSP 可能拦截 javascript: 协议，导致全页刷新 |
| V1→V2 | 点击事件 | `@click="navigate(item)"` | `@click="onNavClick()"` | router-link 自带导航，只需关闭移动端菜单 |
| V1→V2 | 分组项路由 | 自定义 navigate 函数 | 直接 `:to="\`/categories/\${child.id}\`"` | 利用 router-link 原生 SPA 导航能力 |

**修改范围（4 处）：**

| 区域 | 链接数 | 路径格式 |
|:----:|:------:|---------|
| 论坛板块 (`navItems`) | 5 个 | `:to="\`/categories/${child.id}\`"` |
| 分组导航 (`categoryGroups` 子项) | 13 个 | `:to="\`/categories/${child.id}\`"` |
| 发现 (`discoverItems`) | 2 个 | `:to="{ path: item.to, query: item.query }"` |
| 个人 (`personalItems`) | 5 个 | `:to="{ path: item.to, query: item.query }"` |

---

### 交互19：行情数据服务单元测试 — Mock 降级 + K 线覆盖

**日期：** 2026-06-16｜**对应文件：** `backend/tests/unit/test_market_service.py`、`backend/app/api/market.py`

**原始提示词：**
```
【测试用例 - 使用 pytest-httpx 或 respx mock】
- 东方财富正常 → 返回东方财富格式数据
- 东方财富超时 → 自动降级到新浪
- 两个数据源都失败 → 返回空数据标记
- K线数据不同周期（日/周/月/5分钟）
- 内置指数返回验证：上证(000001)，沪深300(000300)，深证成指(399001)
```

**AI输出摘要：**
使用 `respx` mock HTTP 请求，对行情数据服务编写了 **12 个测试用例**：

**指数查询测试（7 个）：**
| 测试 | 场景 | 验证点 |
|:----:|------|--------|
| `test_eastmoney_success` | 东方财富正常返回 | 价格/涨跌幅/涨跌额/涨跌方向 |
| `test_eastmoney_timeout_falls_back_to_sina` | 东方财富超时 | 自动降级到新浪，message 含 "sina" |
| `test_both_sources_fail_returns_fallback` | 两个都失败 | 返回空数据标记，price=None |
| `test_eastmoney_empty_data_falls_back` | 东方财富 data=None | 降级到新浪 |
| `test_multiple_indices` | 多个指数同时查询 | 返回多个结果，涨跌方向正确 |
| `test_default_indices_when_no_secids` | 不传 secids | 使用默认列表（3个指数） |
| `test_specific_index_code` | 特定指数代码 | 上证000001/深证399001 |

**K 线查询测试（5 个）：**
| 测试 | 场景 | 验证点 |
|:----:|------|--------|
| `test_kline_normal` | 正常 K 线数据 | 日期/开/高/低/收/成交量 |
| `test_kline_empty_response` | K 线空 data | 返回空数组 |
| `test_kline_network_error` | K 线网络错误 | 返回 500+空数组 |
| `test_kline_different_periods` | 日线(klt=101)/周线(klt=102) | 不同周期均可正常解析 |
| `test_kline_partial_data_skipped` | 部分数据字段不足 | 跳过异常行 |

**可能存在的问题：**
1. `respx` 的 mock 路由必须与真实代码中的 URL 完全一致，否则不会生效
2. 新浪财经返回 GB18030 编码，mock 内容需 `.encode("gb18030")`
3. 多个 mock 路由在同一测试中共存可能导致路由匹配错误

**迭代优化：**
```
V1.1：东方财富空 data 场景增加 None 处理（data.diff 可能为 None）
V1.1：K线异常行跳过逻辑增加字段数不足5个时的容错
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前 | 修改后 | 修改原因 |
|:----:|--------|-------|-------|---------|
| V1→V2 | 空 data 处理 | 未测试 | 增加 `test_eastmoney_empty_data_falls_back` | 真实场景中 API 可能返回空 data |
| V1→V2 | K 线异常行 | 未测试 | 增加 `test_kline_partial_data_skipped` | 外部数据格式不稳定 |
| V1→V2 | 新浪编码 | 无 | 新浪 mock 使用 `encode("gb18030")` | 与实际编码一致 |

---

### 交互20：生成接口测试 — 邮箱认证 + 禁言功能

**日期：** 2026-06-17｜**对应文件：** `backend/tests/test_email_auth_api.py`、`backend/tests/test_admin_mute_api.py`

**原始提示词：**
```
为以下端点生成TestClient + SQLite接口测试：
- POST /auth/email/send-code, /auth/email/verify-code, /auth/email/register
- 管理员禁言/解禁、被禁言用户发帖/评论限制、通知生成、权限验证
独立可执行脚本（python test_xxx.py）。
```

**AI输出摘要：**

| 测试文件 | 用例数 | 覆盖点 |
|---------|:------:|--------|
| `test_email_auth_api.py` | 15 | 发送验证码(3种类型)、校验(正确/错误/不存在)、注册(正常/重复/未验证)、登录、资料更新 |
| `test_admin_mute_api.py` | 15 | 禁言/解禁、发帖限制(403)、评论限制(403)、通知生成、权限验证 |

**可能存在的问题：**
reset-password 接口 schema 中 phone 字段 regex 仅限制 11 位数字，不支持邮箱重置密码。

**迭代优化：**
```
V1.1：修改phone字段正则表达式，兼容手机号或邮箱两种格式
```

**人工修改迭代过程：**

| 轮次 | 修改项 | 修改前（AI生成） | 修改后（人工修正） | 修改原因 |
|------|--------|-----------------|-------------------|---------|
| V1→V2 | 密码重置 | phone仅限11位数字 | 支持手机号或邮箱两种格式 | 邮箱注册用户无法重置 |

---

### 最终测试统计

| 类别 | 文件数 | 用例数 | 通过率 |
|:----:|:------:|:------:|:------:|
| 单元测试 | 15 | 215 | 100% |
| 接口测试 | 14 | ~280 | 100% |
| 功能测试 | 3 | ~39 | 100% |
| **总计** | **32** | **~534** | **100%** |

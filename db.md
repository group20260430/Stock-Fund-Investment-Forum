# 数据库设计文档 (Database Design)

## 项目名称：股票基金投资论坛 (Stock Fund Investment Forum)

**版本：** v1.0  
**数据库：** MySQL 8.0+  
**字符集：** utf8mb4 / utf8mb4_unicode_ci  
**存储引擎：** InnoDB  
**ORM：** SQLAlchemy 2.0  
**最后更新：** 2026-06-19  
**设计者：** 陶畅（后端开发 A）

---

## 一、数据库概述

### 1.1 基本信息

| 项目 | 说明 |
|------|------|
| 数据库名 | `stock_fund_forum` |
| 默认字符集 | `utf8mb4` |
| 默认排序规则 | `utf8mb4_unicode_ci` |
| 存储引擎 | InnoDB（支持事务、外键、行级锁） |
| 总计表数 | **27 张表** |

### 1.2 设计原则

1. **规范化**：遵循第三范式（3NF），消除数据冗余，保证数据一致性
2. **性能优化**：对高频查询字段建立索引，适度反规范化（如计数冗余字段）
3. **扩展性**：使用 ENUM 类型便于后续扩展状态值；JSON 类型存储灵活结构
4. **数据完整性**：外键约束 + 唯一约束 + NOT NULL 约束确保数据质量
5. **安全性**：密码 bcrypt 哈希存储，敏感 PII 字段预留加密存储空间
6. **可追溯**：关键操作（审核、封禁、认证）均记录操作人和时间戳

### 1.3 模块划分

```
stock_fund_forum
├── 用户系统 (5 表)
│   ├── users                   用户账户
│   ├── verification_codes      短信验证码
│   ├── certifications          实名认证记录
│   ├── risk_assessments        风险评估记录
│   └── refresh_tokens          JWT 刷新令牌
├── 内容系统 (11 表)
│   ├── categories              内容板块
│   ├── posts                   帖子
│   ├── comments                评论
│   ├── post_tags               帖子标签
│   ├── attachments             文件附件
│   ├── likes                   点赞记录
│   ├── favorite_folders        收藏文件夹
│   ├── favorites               收藏记录
│   ├── shares                  转发记录
│   ├── vote_options            投票选项
│   └── vote_records            投票记录
├── 社交系统 (5 表)
│   ├── follows                 关注关系
│   ├── starred_users           星标用户
│   ├── groups                  投资群组
│   ├── group_members           群组成员
│   └── messages                私信
├── 管理运营 (4 表)
│   ├── reports                 举报记录
│   ├── review_logs             审核日志
│   ├── ban_records             封禁记录
│   └── sensitive_words         敏感词库
└── 统计日志 (2 表)
    ├── daily_stats              每日统计
    └── user_activity_log        用户活动日志
```

---

## 二、实体关系总览

```
                                    ┌─────────────────┐
                                    │    users         │
                                    │  (用户账户)       │
                                    └────────┬────────┘
            ┌─────────────────────────────────┼─────────────────────────────────────┐
            │                    │            │            │              │          │
            ▼                    ▼            ▼            ▼              ▼          ▼
   ┌──────────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ verification_    │  │ certifi- │  │ risk_    │  │ refresh_ │  │ follows  │  │ starred_ │
   │ codes            │  │ cations  │  │ assessments│ │ tokens   │  │(关注关系) │  │ users    │
   │ (验证码)          │  │ (实名认证)│  │ (风险评估) │  │ (刷新令牌)│  └──────────┘  │ (星标用户) │
   └──────────────────┘  └──────────┘  └──────────┘  └──────────┘                └──────────┘

   ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
   │                                        users (用户)                                          │
   └─────────────────────────────────────────────────────────────────────────────────────────────┘
            │                    │            │            │              │          │
            ▼                    ▼            ▼            ▼              ▼          ▼
   ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │    posts     │  │ comments │  │  likes   │  │ favorites│  │  shares  │  │ ban_     │
   │   (帖子)     │  │ (评论)    │  │ (点赞)    │  │ (收藏)    │  │ (转发)    │  │ records  │
   └──────┬───────┘  └────┬─────┘  └──────────┘  └────┬─────┘  └──────────┘  │ (封禁记录) │
          │               │                           │                      └──────────┘
          ▼               │                           ▼
   ┌──────────────┐       │                    ┌──────────────┐
   │  categories  │       │                    │   favorite   │
   │  (板块分类)   │       │                    │   _folders   │
   └──────────────┘       │                    │  (收藏文件夹)  │
          ▲               │                    └──────────────┘
          │               │
   ┌──────┴───────┐       │       ┌──────────┐  ┌──────────┐  ┌──────────┐
   │              │       │       │ groups   │  │ group_   │  │ messages │
   ┌──────────┐  ┌──────────┐     │ (群组)    │  │ members  │  │ (私信)    │
   │ attach-  │  │  post_   │     └────┬─────┘  │ (群组成员) │  └──────────┘
   │ ments    │  │  tags    │          │        └──────────┘
   │ (附件)    │  │ (标签)    │          │
   └──────────┘  └──────────┘     ┌────┴──────────────────────┐
                                  │                           │
   ┌──────────┐  ┌──────────┐    ┌──────────┐    ┌──────────────┐
   │  vote_   │  │ reports  │    │  review  │    │  sensitive   │
   │ options  │  │ (举报)    │    │  _logs   │    │  _words      │
   │ (投票选项)│  └──────────┘    │ (审核日志) │    │  (敏感词库)   │
   └──────────┘                  └──────────┘    └──────────────┘

   ┌──────────────┐  ┌──────────────────┐
   │ daily_stats  │  │ user_activity_log│
   │ (每日统计)    │  │ (用户活动日志)     │
   └──────────────┘  └──────────────────┘
```

### 核心实体关系（文字描述）

| 关系 | 类型 | 说明 |
|------|------|------|
| User → Post | 1:N | 一个用户可发布多个帖子 |
| User → Comment | 1:N | 一个用户可发表多个评论 |
| User → Certification | 1:N | 一个用户可多次提交认证 |
| User → RiskAssessment | 1:N | 一个用户可多次进行风险评估 |
| Category → Post | 1:N | 一个板块包含多个帖子 |
| Post → Comment | 1:N | 一个帖子包含多个评论 |
| Post → Attachment | 1:N | 一个帖子可附带多个文件 |
| Post → VoteOption | 1:N | 一个投票帖包含多个选项 |
| Comment → Comment | 1:N (自引用) | 评论支持嵌套回复（楼中楼） |
| User → Follow → User | M:N | 用户之间多对多关注关系 |
| User → Favorite → Post | M:N | 用户收藏帖子（通过收藏夹） |
| User → Like → (Post/Comment) | M:N (多态) | 用户点赞帖子或评论 |
| User → Group → User | M:N | 用户通过 group_members 关联群组 |
| User → Message → User | 1:N | 用户间私信 |

---

## 三、表结构详细设计

### 模块1：用户系统 (User System)

---

#### 3.1.1 `users` — 用户账户表

**说明：** 存储所有注册用户的基本信息、认证状态、投资偏好。系统核心表。

```sql
CREATE TABLE IF NOT EXISTS users (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '用户ID',
  phone           VARCHAR(11)    NOT NULL UNIQUE              COMMENT '手机号，11位数字',
  email           VARCHAR(120)   NULL                         COMMENT '邮箱地址',
  password_hash   VARCHAR(255)   NOT NULL                     COMMENT 'bcrypt密码哈希',
  nickname        VARCHAR(50)    NOT NULL                     COMMENT '用户昵称，2~20字符',
  avatar_url      VARCHAR(500)   NULL                         COMMENT '头像URL',
  bio             VARCHAR(500)   NULL                         COMMENT '个人简介',
  role            ENUM('user','moderator','admin')
                                  NOT NULL DEFAULT 'user'     COMMENT '角色：user=普通用户, moderator=版主, admin=管理员',
  auth_level      ENUM('none','basic','verified','professional')
                                  NOT NULL DEFAULT 'none'     COMMENT '认证等级：none=未认证, basic=手机验证, verified=实名认证, professional=专业认证',
  risk_level      ENUM('conservative','moderate','aggressive')
                                  NULL                         COMMENT '风险偏好：conservative=保守, moderate=稳健, aggressive=激进',
  status          ENUM('active','disabled')
                                  NOT NULL DEFAULT 'active'    COMMENT '账户状态：active=正常, disabled=封禁',
  register_type   ENUM('phone','email','wechat','weibo')
                                  NOT NULL DEFAULT 'phone'    COMMENT '注册方式',
  investment_tags JSON            NULL                         COMMENT '投资标签，如["价值投资","消费","A股"]',
  follow_markets  JSON            NULL                         COMMENT '关注市场，如["A股","港股","美股"]',
  is_professional TINYINT(1)      NOT NULL DEFAULT 0          COMMENT '是否专业认证用户',
  ban_expires_at  TIMESTAMP       NULL                         COMMENT '封禁到期时间，NULL为永久封禁',
  banned_reason   VARCHAR(255)    NULL                         COMMENT '封禁原因',
  followers_count INT UNSIGNED    NOT NULL DEFAULT 0          COMMENT '粉丝数（冗余，提升查询性能）',
  following_count INT UNSIGNED    NOT NULL DEFAULT 0          COMMENT '关注数（冗余，提升查询性能）',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '注册时间',
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP  COMMENT '最后更新时间',

  INDEX idx_users_phone         (phone),
  INDEX idx_users_email         (email),
  INDEX idx_users_status_created (status, created_at),
  INDEX idx_users_role          (role),
  INDEX idx_users_auth_level    (auth_level),
  INDEX idx_users_ban_expires   (ban_expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户账户表';
```

**字段变更说明（相对于旧版 schema）：**

| 变更类型 | 字段 | 说明 |
|----------|------|------|
| 新增 | `register_type` | 记录注册方式 |
| 新增 | `ban_expires_at` | 支持临时封禁，到期自动解封 |
| 新增 | `banned_reason` | 记录封禁原因 |
| 新增 | `followers_count` | 粉丝数冗余，避免频繁 COUNT |
| 新增 | `following_count` | 关注数冗余，避免频繁 COUNT |

---

#### 3.1.2 `verification_codes` — 短信验证码表

**说明：** 存储发送的验证码及其有效期，支持注册、登录、重置密码三种场景。

```sql
CREATE TABLE IF NOT EXISTS verification_codes (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  phone           VARCHAR(11)    NOT NULL                     COMMENT '手机号',
  code            VARCHAR(10)    NOT NULL                     COMMENT '6位验证码',
  type            ENUM('register','login','reset_password')
                                  NOT NULL                     COMMENT '验证码类型',
  expires_at      TIMESTAMP      NOT NULL                     COMMENT '过期时间（默认5分钟）',
  is_used         TINYINT(1)     NOT NULL DEFAULT 0          COMMENT '是否已使用',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '发送时间',

  INDEX idx_vc_phone_type        (phone, type),
  INDEX idx_vc_phone_code        (phone, code),
  INDEX idx_vc_expires           (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='短信验证码表';
```

---

#### 3.1.3 `certifications` — 实名认证记录表

**说明：** 存储用户实名认证的申请和审核记录，敏感信息应在应用层加密后存储。

```sql
CREATE TABLE IF NOT EXISTS certifications (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '认证记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '申请人用户ID',
  real_name       VARCHAR(255)    NOT NULL                     COMMENT '真实姓名（应用层AES加密存储）',
  id_number       VARCHAR(255)    NOT NULL                     COMMENT '身份证号（应用层AES加密存储）',
  id_card_front   VARCHAR(500)    NOT NULL                     COMMENT '身份证正面照片URL',
  id_card_back    VARCHAR(500)    NOT NULL                     COMMENT '身份证反面照片URL',
  status          ENUM('pending','approved','rejected')
                                  NOT NULL DEFAULT 'pending'   COMMENT '审核状态',
  reviewer_id     BIGINT UNSIGNED NULL                         COMMENT '审核人ID（管理员）',
  review_comment  VARCHAR(500)    NULL                         COMMENT '审核意见',
  reviewed_at     TIMESTAMP       NULL                         COMMENT '审核时间',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '申请时间',

  CONSTRAINT fk_cert_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_cert_reviewer
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
    ON DELETE SET NULL,

  INDEX idx_cert_user    (user_id),
  INDEX idx_cert_status  (status),
  INDEX idx_cert_reviewer(reviewer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='实名认证记录表';
```

> ⚠️ **安全提示：** `real_name` 和 `id_number` 字段存储的是应用层 AES-256 加密后的密文，数据库层面不存储明文。密钥通过环境变量注入，不写入代码仓库。

---

#### 3.1.4 `risk_assessments` — 风险评估记录表

**说明：** 存储用户每次风险评估问卷的答案和评分结果，支持多次评估历史追溯。

```sql
CREATE TABLE IF NOT EXISTS risk_assessments (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '评估记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  answers         JSON            NOT NULL                     COMMENT '答案数组[{"question_id":1,"answer":"A"},...]',
  total_questions INT             NOT NULL DEFAULT 15         COMMENT '题目总数',
  score           INT             NOT NULL                     COMMENT '风险评分',
  max_score       INT             NOT NULL DEFAULT 100        COMMENT '满分值',
  risk_level      ENUM('conservative','moderate','aggressive')
                                  NOT NULL                     COMMENT '评估结果风险等级',
  suggestion      TEXT            NULL                         COMMENT '系统建议文本',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '评估时间',

  CONSTRAINT fk_risk_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_risk_user (user_id),
  INDEX idx_risk_level(risk_level),
  INDEX idx_risk_time (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='风险评估记录表';
```

---

#### 3.1.5 `refresh_tokens` — JWT 刷新令牌表

**说明：** 存储已签发的 Refresh Token，支持令牌轮换、撤销和过期管理。

```sql
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '令牌记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '所属用户ID',
  token_hash      VARCHAR(255)    NOT NULL                     COMMENT 'Token的SHA-256哈希（不存明文）',
  expires_at      TIMESTAMP       NOT NULL                     COMMENT '过期时间（7天）',
  is_revoked      TINYINT(1)     NOT NULL DEFAULT 0          COMMENT '是否已撤销',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '签发时间',

  CONSTRAINT fk_rt_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_rt_hash   (token_hash),
  INDEX idx_rt_user          (user_id),
  INDEX idx_rt_expires       (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='JWT刷新令牌表';
```

> ⚠️ **安全提示：** `token_hash` 存储的是 Refresh Token 原文的 SHA-256 哈希值。Token 原文仅在签发时通过 API 返回给客户端一次，此后不再存储。

---

### 模块2：内容系统 (Content System)

---

#### 3.2.1 `categories` — 内容板块表（扩展）

**说明：** 论坛的内容分类/板块。管理员可增删改。

```sql
CREATE TABLE IF NOT EXISTS categories (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '板块ID',
  name            VARCHAR(50)    NOT NULL UNIQUE              COMMENT '板块名称',
  description     VARCHAR(255)   NULL                         COMMENT '板块描述',
  sort_order      INT            NOT NULL DEFAULT 0            COMMENT '排序序号，越小越靠前',
  is_active       TINYINT(1)    NOT NULL DEFAULT 1            COMMENT '是否启用：1=启用, 0=停用',
  post_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '帖子数（冗余，提升查询性能）',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '创建时间',

  INDEX idx_cat_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='内容板块表';
```

**字段变更说明：**

| 变更类型 | 字段 | 说明 |
|----------|------|------|
| 新增 | `is_active` | 支持板块软删除/停用 |
| 新增 | `post_count` | 帖子数冗余 |

---

#### 3.2.2 `posts` — 帖子表（扩展）

**说明：** 论坛的核心内容表。支持普通帖、长文、投票、动态四种类型。

```sql
CREATE TABLE IF NOT EXISTS posts (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '帖子ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '作者用户ID',
  category_id     BIGINT UNSIGNED NOT NULL                    COMMENT '所属板块ID',
  title           VARCHAR(120)    NOT NULL                     COMMENT '帖子标题，1~120字符',
  content         TEXT            NOT NULL                     COMMENT '帖子正文（支持Markdown/HTML）',
  post_type       ENUM('normal','long_article','poll','moment')
                                  NOT NULL DEFAULT 'normal'    COMMENT '帖子类型：normal=普通帖, long_article=长文, poll=投票帖, moment=动态',
  status          ENUM('draft','published','reviewing','rejected')
                                  NOT NULL DEFAULT 'published' COMMENT '状态：draft=草稿, published=已发布, reviewing=审核中, rejected=已拒绝',
  is_elite        TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否精华帖',
  tags            JSON            NULL                         COMMENT '标签数组，如["A股","盘面分析"]',
  view_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '浏览次数',
  like_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '点赞数（冗余）',
  comment_count   INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '评论数（冗余）',
  collect_count   INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '收藏数（冗余）',
  share_count     INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '转发数（冗余）',
  last_activity_at TIMESTAMP     NULL                         COMMENT '最后活动时间（用于热度排序）',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '发布时间',
  updated_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP   COMMENT '最后编辑时间',

  CONSTRAINT fk_posts_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_posts_category
    FOREIGN KEY (category_id) REFERENCES categories(id)
    ON DELETE RESTRICT,

  INDEX idx_posts_category_created (category_id, status, created_at),
  INDEX idx_posts_user_created     (user_id, created_at),
  INDEX idx_posts_status           (status),
  INDEX idx_posts_post_type        (post_type),
  INDEX idx_posts_is_elite         (is_elite),
  INDEX idx_posts_hot              (status, last_activity_at),
  FULLTEXT INDEX ft_posts_search   (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='帖子表';
```

**字段变更说明：**

| 变更类型 | 字段 | 说明 |
|----------|------|------|
| 新增 | `post_type` | 支持普通帖/长文/投票/动态 |
| 新增 | `is_elite` | 精华帖标记 |
| 新增 | `tags` | JSON 标签数组 |
| 新增 | `collect_count` | 收藏数冗余 |
| 新增 | `share_count` | 转发数冗余 |
| 新增 | `last_activity_at` | 最后活动时间 |

---

#### 3.2.3 `comments` — 评论表（扩展）

**说明：** 帖子评论，支持嵌套回复（楼中楼）和 @提及。

```sql
CREATE TABLE IF NOT EXISTS comments (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '评论ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '所属帖子ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '评论者用户ID',
  parent_id       BIGINT UNSIGNED NULL                         COMMENT '父评论ID（一级评论为NULL，二级回复指向一级评论）',
  reply_to_id     BIGINT UNSIGNED NULL                         COMMENT '被回复的评论ID（用于@提及跳转）',
  content         TEXT            NOT NULL                     COMMENT '评论正文，最多2000字符',
  like_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '点赞数（冗余）',
  status          ENUM('published','reviewing','rejected')
                                  NOT NULL DEFAULT 'published' COMMENT '状态',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '评论时间',
  updated_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP   COMMENT '编辑时间',

  CONSTRAINT fk_comments_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_comments_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_comments_parent
    FOREIGN KEY (parent_id) REFERENCES comments(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_comments_reply_to
    FOREIGN KEY (reply_to_id) REFERENCES comments(id)
    ON DELETE SET NULL,

  INDEX idx_comments_post_created (post_id, status, created_at),
  INDEX idx_comments_user         (user_id, created_at),
  INDEX idx_comments_parent       (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='评论表';
```

**字段变更说明：**

| 变更类型 | 字段 | 说明 |
|----------|------|------|
| 新增 | `reply_to_id` | 精确追踪 @回复目标 |
| 新增 | `like_count` | 评论点赞数冗余 |

---

#### 3.2.4 `post_tags` — 帖子标签关联表

**说明：** 帖子与标签的多对多细粒度关系表（作为 `posts.tags` JSON 字段的补充，用于跨帖标签聚合查询）。

```sql
CREATE TABLE IF NOT EXISTS post_tags (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '关联ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '帖子ID',
  tag_name        VARCHAR(50)     NOT NULL                     COMMENT '标签名称',

  CONSTRAINT fk_pt_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_pt_post_tag (post_id, tag_name),
  INDEX idx_pt_tag            (tag_name),
  INDEX idx_pt_post           (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='帖子标签关联表';
```

---

#### 3.2.5 `attachments` — 文件附件表

**说明：** 帖子附带的文件（PDF报告、Excel数据、图片等）。

```sql
CREATE TABLE IF NOT EXISTS attachments (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '附件ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '所属帖子ID',
  file_name       VARCHAR(255)    NOT NULL                     COMMENT '原始文件名',
  file_url        VARCHAR(500)    NOT NULL                     COMMENT '文件存储URL',
  file_size       INT UNSIGNED   NOT NULL                     COMMENT '文件大小（字节）',
  file_type       VARCHAR(50)     NOT NULL                     COMMENT 'MIME类型，如application/pdf',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '上传时间',

  CONSTRAINT fk_att_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  INDEX idx_att_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='文件附件表';
```

> ⚠️ **约束：** 应用层需限制文件类型为 PDF/Excel/图片，单文件 ≤ 10MB。

---

#### 3.2.6 `likes` — 点赞记录表（统一）

**说明：** 统一的点赞记录表，通过 `target_type` 区分点赞对象（帖子或评论）。

```sql
CREATE TABLE IF NOT EXISTS likes (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '点赞记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '点赞用户ID',
  target_type     ENUM('post','comment')
                                  NOT NULL                     COMMENT '目标类型：post=帖子, comment=评论',
  target_id       BIGINT UNSIGNED NOT NULL                    COMMENT '目标ID（帖子ID或评论ID）',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '点赞时间',

  CONSTRAINT fk_likes_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_likes_unique  (user_id, target_type, target_id),
  INDEX idx_likes_target         (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='点赞记录表（统一帖子与评论）';
```

> **设计说明：** 采用多态关联（polymorphic association）而非两张独立表，简化业务逻辑。唯一索引确保同一用户对同一目标只能点赞一次（Toggle 模式）。

---

#### 3.2.7 `favorite_folders` — 收藏文件夹表

**说明：** 用户的收藏夹分组管理。

```sql
CREATE TABLE IF NOT EXISTS favorite_folders (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '文件夹ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  name            VARCHAR(50)     NOT NULL DEFAULT '默认收藏夹' COMMENT '文件夹名称',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '创建时间',

  CONSTRAINT fk_ff_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_ff_user_name (user_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='收藏文件夹表';
```

---

#### 3.2.8 `favorites` — 收藏记录表

**说明：** 用户收藏帖子的关联记录。

```sql
CREATE TABLE IF NOT EXISTS favorites (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '收藏记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '帖子ID',
  folder_id       BIGINT UNSIGNED NOT NULL                    COMMENT '所属收藏夹ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '收藏时间',

  CONSTRAINT fk_fav_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_fav_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_fav_folder
    FOREIGN KEY (folder_id) REFERENCES favorite_folders(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_fav_unique (user_id, post_id),
  INDEX idx_fav_user_folder  (user_id, folder_id),
  INDEX idx_fav_post         (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='收藏记录表';
```

---

#### 3.2.9 `shares` — 转发记录表

**说明：** 记录用户转发帖子的行为。

```sql
CREATE TABLE IF NOT EXISTS shares (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '转发记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '转发用户ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '被转发帖子ID',
  share_type      ENUM('timeline','message','group')
                                  NOT NULL                     COMMENT '转发类型：timeline=动态, message=私信, group=群组',
  comment         VARCHAR(500)    NULL                         COMMENT '转发附言',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '转发时间',

  CONSTRAINT fk_share_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_share_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  INDEX idx_share_user (user_id, created_at),
  INDEX idx_share_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='转发记录表';
```

---

#### 3.2.10 `vote_options` — 投票选项表

**说明：** 投票类型帖子的选项定义，以及每个选项的得票计数。

```sql
CREATE TABLE IF NOT EXISTS vote_options (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '选项ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '投票帖子ID',
  label           VARCHAR(200)    NOT NULL                     COMMENT '选项文本',
  vote_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '得票数（冗余，提升查询性能）',
  sort_order      INT            NOT NULL DEFAULT 0            COMMENT '显示顺序',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '创建时间',

  CONSTRAINT fk_vo_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  INDEX idx_vo_post (post_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='投票选项表';
```

---

##### 3.2.11 `vote_records` — 投票记录表

**说明：** 记录每个用户对投票选项的选择，防止重复投票并支持更改投票。

```sql
CREATE TABLE IF NOT EXISTS vote_records (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '投票记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '投票用户ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '投票帖子ID',
  option_id       BIGINT UNSIGNED NOT NULL                    COMMENT '选择的选项ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '投票时间',
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP   COMMENT '更改投票时间',

  CONSTRAINT fk_vr_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_vr_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_vr_option
    FOREIGN KEY (option_id) REFERENCES vote_options(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_vr_user_post  (user_id, post_id),
  INDEX idx_vr_option           (option_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户投票记录表';
```

---

### 模块3：社交系统 (Social System)

---

#### 3.3.1 `follows` — 关注关系表（保持不变）

**说明：** 用户之间的关注关系。已有表结构完整，无需修改。

```sql
CREATE TABLE IF NOT EXISTS follows (
  follower_id     BIGINT UNSIGNED NOT NULL                    COMMENT '关注者用户ID',
  following_id    BIGINT UNSIGNED NOT NULL                    COMMENT '被关注者用户ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '关注时间',

  PRIMARY KEY (follower_id, following_id),

  CONSTRAINT fk_follows_follower
    FOREIGN KEY (follower_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_follows_following
    FOREIGN KEY (following_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_follows_following (following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='关注关系表';
```

> **注意：** `followers_count` 和 `following_count` 冗余在 `users` 表中，关注/取关时需同步更新。

---

#### 3.3.2 `starred_users` — 星标用户表

**说明：** 用户标记的特别关注/星标用户列表。

```sql
CREATE TABLE IF NOT EXISTS starred_users (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  starred_user_id BIGINT UNSIGNED NOT NULL                    COMMENT '被星标的用户ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '设置时间',

  CONSTRAINT fk_su_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_su_starred
    FOREIGN KEY (starred_user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_su_unique (user_id, starred_user_id),
  INDEX idx_su_user          (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='星标用户表';
```

---

#### 3.3.3 `groups` — 投资群组表

**说明：** 用户创建的讨论群组。

```sql
CREATE TABLE IF NOT EXISTS `groups` (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '群组ID',
  name            VARCHAR(50)    NOT NULL UNIQUE              COMMENT '群组名称',
  description     VARCHAR(500)   NULL                         COMMENT '群组描述',
  avatar_url      VARCHAR(500)   NULL                         COMMENT '群组头像URL',
  visibility      ENUM('public','private')
                                  NOT NULL DEFAULT 'public'    COMMENT '可见性：public=公开, private=私密',
  need_approval   TINYINT(1)    NOT NULL DEFAULT 0            COMMENT '加入是否需要管理员审批',
  creator_id      BIGINT UNSIGNED NOT NULL                    COMMENT '创建者用户ID',
  member_count    INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '成员数（冗余）',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '创建时间',
  updated_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP   COMMENT '更新时间',

  CONSTRAINT fk_group_creator
    FOREIGN KEY (creator_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_groups_visibility (visibility),
  INDEX idx_groups_creator    (creator_id),
  INDEX idx_groups_name       (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='投资群组表';
```

> **注意：** `groups` 是 MySQL 保留字，SQL 中需用反引号包裹。

---

#### 3.3.4 `group_members` — 群组成员表

**说明：** 群组与用户的多对多关系，包含成员角色和加入审批状态。

```sql
CREATE TABLE IF NOT EXISTS group_members (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '成员记录ID',
  group_id        BIGINT UNSIGNED NOT NULL                    COMMENT '群组ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  role            ENUM('owner','admin','member')
                                  NOT NULL DEFAULT 'member'    COMMENT '角色：owner=群主, admin=管理员, member=普通成员',
  status          ENUM('pending','approved','rejected')
                                  NOT NULL DEFAULT 'approved'  COMMENT '加入状态（need_approval=1时生效）',
  joined_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '加入时间',

  CONSTRAINT fk_gm_group
    FOREIGN KEY (group_id) REFERENCES `groups`(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_gm_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_gm_unique  (group_id, user_id),
  INDEX idx_gm_user           (user_id),
  INDEX idx_gm_status         (group_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='群组成员表';
```

---

#### 3.3.5 `messages` — 私信表

**说明：** 用户间点对点私信。

```sql
CREATE TABLE IF NOT EXISTS messages (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '消息ID',
  sender_id       BIGINT UNSIGNED NOT NULL                    COMMENT '发送者用户ID',
  receiver_id     BIGINT UNSIGNED NOT NULL                    COMMENT '接收者用户ID',
  content         TEXT            NOT NULL                     COMMENT '消息正文，最多5000字符',
  message_type    ENUM('text','image','file')
                                  NOT NULL DEFAULT 'text'      COMMENT '消息类型',
  attachment_url  VARCHAR(500)    NULL                         COMMENT '附件URL（图片/文件）',
  is_read         TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否已读',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '发送时间',

  CONSTRAINT fk_msg_sender
    FOREIGN KEY (sender_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_msg_receiver
    FOREIGN KEY (receiver_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_msg_conversation (sender_id, receiver_id, created_at),
  INDEX idx_msg_receiver_unread (receiver_id, is_read, created_at),
  INDEX idx_msg_created         (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='私信表';
```

> **查询会话列表策略：** 使用子查询或 GROUP BY 按 `LEAST(sender_id, receiver_id), GREATEST(sender_id, receiver_id)` 分组获取每个会话的最新消息。

---

### 模块4：管理运营系统 (Admin & Operations)

---

#### 3.4.1 `reports` — 举报记录表

**说明：** 用户对违规内容（帖子、评论、用户）的举报。

```sql
CREATE TABLE IF NOT EXISTS reports (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '举报ID',
  reporter_id     BIGINT UNSIGNED NOT NULL                    COMMENT '举报人用户ID',
  target_type     ENUM('post','comment','user')
                                  NOT NULL                     COMMENT '举报目标类型',
  target_id       BIGINT UNSIGNED NOT NULL                    COMMENT '举报目标ID',
  reason          ENUM('fake_info','personal_attack','illegal_stock_promotion','spam','other')
                                  NOT NULL                     COMMENT '举报原因',
  description     VARCHAR(500)    NULL                         COMMENT '举报补充说明',
  status          ENUM('pending','resolved','dismissed')
                                  NOT NULL DEFAULT 'pending'   COMMENT '处理状态',
  handler_id      BIGINT UNSIGNED NULL                         COMMENT '处理人ID（管理员）',
  handle_comment  VARCHAR(500)    NULL                         COMMENT '处理意见',
  handled_at      TIMESTAMP       NULL                         COMMENT '处理时间',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '举报时间',

  CONSTRAINT fk_rep_reporter
    FOREIGN KEY (reporter_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_rep_handler
    FOREIGN KEY (handler_id) REFERENCES users(id)
    ON DELETE SET NULL,

  UNIQUE INDEX idx_rep_unique  (reporter_id, target_type, target_id),
  INDEX idx_rep_status         (status, created_at),
  INDEX idx_rep_target         (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='举报记录表';
```

---

#### 3.4.2 `review_logs` — 审核日志表

**说明：** 管理员内容审核的完整操作记录，支持追溯。

```sql
CREATE TABLE IF NOT EXISTS review_logs (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '日志ID',
  target_type     ENUM('post','comment')
                                  NOT NULL                     COMMENT '审核目标类型',
  target_id       BIGINT UNSIGNED NOT NULL                    COMMENT '审核目标ID',
  reviewer_id     BIGINT UNSIGNED NOT NULL                    COMMENT '审核人ID（管理员）',
  action          ENUM('approve','reject','edit')
                                  NOT NULL                     COMMENT '审核操作',
  comment         VARCHAR(500)    NULL                         COMMENT '审核意见',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '审核时间',

  CONSTRAINT fk_rl_reviewer
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_rl_target     (target_type, target_id),
  INDEX idx_rl_reviewer   (reviewer_id, created_at),
  INDEX idx_rl_action     (action, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='审核日志表';
```

---

#### 3.4.3 `ban_records` — 封禁记录表

**说明：** 管理员对用户的封禁/解封操作历史。

```sql
CREATE TABLE IF NOT EXISTS ban_records (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '被封禁用户ID',
  admin_id        BIGINT UNSIGNED NOT NULL                    COMMENT '操作管理员ID',
  action          ENUM('ban','unban')
                                  NOT NULL                     COMMENT '操作类型',
  reason          VARCHAR(500)    NULL                         COMMENT '封禁/解封原因',
  duration_hours  INT UNSIGNED   NULL                         COMMENT '封禁时长（小时），NULL为永久封禁',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '操作时间',

  CONSTRAINT fk_br_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_br_admin
    FOREIGN KEY (admin_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_br_user  (user_id, created_at),
  INDEX idx_br_admin (admin_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='封禁记录表';
```

---

#### 3.4.4 `sensitive_words` — 敏感词库表

**说明：** 内容自动审核的敏感词词典。管理员可维护。

```sql
CREATE TABLE IF NOT EXISTS sensitive_words (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '词条ID',
  word            VARCHAR(100)    NOT NULL UNIQUE              COMMENT '敏感词',
  level           ENUM('block','review','warn')
                                  NOT NULL DEFAULT 'review'    COMMENT '触发级别：block=直接拦截, review=进入人工审核, warn=标记提醒',
  category        VARCHAR(50)     NULL                         COMMENT '词条分类',
  is_active       TINYINT(1)     NOT NULL DEFAULT 1            COMMENT '是否启用',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '添加时间',

  INDEX idx_sw_level (level, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='敏感词库表';
```

---

### 模块5：统计与日志系统 (Statistics & Logging)

---

#### 3.5.1 `daily_stats` — 每日统计表

**说明：** 预计算的每日运营统计数据，支持管理后台趋势图表查询。

```sql
CREATE TABLE IF NOT EXISTS daily_stats (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '统计ID',
  stat_date       DATE            NOT NULL UNIQUE              COMMENT '统计日期',
  dau             INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '日活跃用户数',
  new_users       INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增注册用户数',
  total_posts     INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增帖子数',
  total_comments  INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增评论数',
  total_likes     INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日点赞数',
  total_shares    INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日转发数',
  reports_count   INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增举报数',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '记录创建时间',
  updated_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP   COMMENT '记录更新时间',

  INDEX idx_ds_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='每日统计表';
```

> **说明：** 该表数据通过定时任务（cron）或应用层每日聚合计算后写入。对于课程项目 MVP 阶段，也可直接从各业务表实时 COUNT 查询。

---

#### 3.5.2 `user_activity_log` — 用户活动日志表

**说明：** 记录用户每日关键活动，用于 DAU 计算和行为分析。

```sql
CREATE TABLE IF NOT EXISTS user_activity_log (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '日志ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  activity_type   ENUM('login','post','comment','like','follow','share','vote')
                                  NOT NULL                     COMMENT '活动类型',
  target_type     VARCHAR(20)     NULL                         COMMENT '活动目标类型',
  target_id       BIGINT UNSIGNED NULL                         COMMENT '活动目标ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                               COMMENT '活动时间',

  CONSTRAINT fk_ual_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_ual_user_date    (user_id, created_at),
  INDEX idx_ual_date_type    (created_at, activity_type),
  INDEX idx_ual_activity     (activity_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户活动日志表';
```

---

## 四、索引汇总

### 4.1 索引策略说明

| 索引类型 | 使用场景 |
|----------|---------|
| **主键索引** | 所有表 id 字段，聚簇索引 |
| **唯一索引** | 防止重复数据（手机号、关注关系、点赞、收藏、举报） |
| **外键索引** | 所有 FOREIGN KEY 字段，加速 JOIN 查询 |
| **复合索引** | 高频查询条件组合，如 `(status, created_at)` 用于分页列表 |
| **全文索引** | `posts.title` 和 `posts.content`，支持中文搜索 |

### 4.2 关键复合索引一览

| 表 | 索引名 | 字段 | 用途 |
|----|--------|------|------|
| users | `idx_users_status_created` | `(status, created_at)` | 管理员用户列表查询 |
| posts | `idx_posts_category_created` | `(category_id, status, created_at)` | 板块帖子列表（最常用） |
| posts | `idx_posts_hot` | `(status, last_activity_at)` | 热榜排序查询 |
| comments | `idx_comments_post_created` | `(post_id, status, created_at)` | 帖子评论列表 |
| messages | `idx_msg_conversation` | `(sender_id, receiver_id, created_at)` | 私信会话查询 |
| messages | `idx_msg_receiver_unread` | `(receiver_id, is_read, created_at)` | 未读消息查询 |
| likes | `idx_likes_unique` | `(user_id, target_type, target_id)` UNIQUE | 防重复点赞 + Toggle 查询 |
| reports | `idx_rep_unique` | `(reporter_id, target_type, target_id)` UNIQUE | 防重复举报 |

---

## 五、种子数据策略

### 5.1 初始化数据

```sql
-- 板块分类（4个初始板块）
INSERT INTO categories (name, description, sort_order) VALUES
  ('股票市场', 'A股、港股、美股等股票市场讨论', 10),
  ('基金投资', '指数基金、主动基金、资产配置讨论', 20),
  ('问答求助', '新手问题、投资知识和工具求助', 30),
  ('投资策略', '价值投资、量化投资和宏观策略讨论', 40);

-- 敏感词初始化（示例）
INSERT INTO sensitive_words (word, level, category) VALUES
  ('非法集资', 'block', '金融违规'),
  ('荐股', 'review', '金融合规'),
  ('内幕消息', 'block', '金融违规'),
  ('保证收益', 'review', '金融合规');
```

### 5.2 开发/测试数据

- 创建 2 个测试用户（密码用 bcrypt 哈希）
- 创建 2~3 条示例帖子
- 创建若干示例评论

详细 seed 脚本见 `database/seed.sql`。

---

## 六、迁移说明（从旧 schema 升级）

### 6.1 变更清单

| 表 | 操作 | 说明 |
|----|------|------|
| `users` | ALTER TABLE | 新增 5 个字段：`register_type`, `ban_expires_at`, `banned_reason`, `followers_count`, `following_count` |
| `categories` | ALTER TABLE | 新增 2 个字段：`is_active`, `post_count` |
| `posts` | ALTER TABLE | 新增 6 个字段：`post_type`, `is_elite`, `tags`, `collect_count`, `share_count`, `last_activity_at`；新增 FULLTEXT 索引 |
| `comments` | ALTER TABLE | 新增 2 个字段：`reply_to_id`, `like_count` |
| 其余 21 张表 | CREATE TABLE | 全新创建 |

### 6.2 升级步骤

1. **备份现有数据库**（如有数据）
2. 执行 ALTER TABLE 语句升级已有表
3. 执行 CREATE TABLE 语句创建新表
4. 验证所有外键约束完整性
5. 执行 `seed.sql` 初始化基础数据

> 项目当前处于早期开发阶段，数据库中仅有种子数据，可直接删除重建。使用完整版 `schema.sql` 即可。

---

## 七、安全设计

### 7.1 数据安全措施

| 措施 | 实现层 | 说明 |
|------|--------|------|
| 密码哈希 | 应用层 (bcrypt) | `users.password_hash` 存储 bcrypt($2b$12) 哈希值 |
| PII 加密 | 应用层 (AES-256) | `certifications.real_name`、`certifications.id_number` 加密存储 |
| 手机号脱敏 | API 响应层 | 返回 `138****8000` 格式 |
| Token 哈希 | 数据库 | `refresh_tokens.token_hash` 存储 SHA-256(原始Token) |
| SQL 注入防护 | ORM 层 | SQLAlchemy 参数化查询，禁止拼接 SQL |
| 文件上传限制 | 应用层 | 类型白名单（PDF/Excel/PNG/JPG），单文件 ≤ 10MB |

### 7.2 访问控制矩阵

| 角色 | 权限范围 |
|------|---------|
| **未登录用户** | 浏览帖子/评论、查看热榜、搜索、查看用户主页 |
| **普通用户 (user)** | 以上 + 发帖/评论、点赞/收藏/转发、关注、举报、私信、加入群组 |
| **版主 (moderator)** | 以上 + 管理指定板块内容、审核帖子/评论 |
| **管理员 (admin)** | 以上 + 全站内容审核、用户管理（封禁/解封）、板块管理、查看统计数据 |

### 7.3 数据保留策略

| 数据类型 | 保留策略 |
|----------|---------|
| 用户账户 | 软删除（status=disabled），不物理删除 |
| 帖子/评论 | 状态标记（rejected），保留内容用于审计 |
| 验证码 | 过期后保留 24h，之后可清理 |
| Refresh Token | 过期或撤销后保留 30 天，之后可清理 |
| 活动日志 | 保留 90 天，之后可归档或清理 |
| 每日统计 | 永久保留（数据量小） |

---

## 八、附录：API 端点与数据库表映射

| API 端点 | 涉及的主要表 |
|----------|-------------|
| POST /auth/register | users, verification_codes |
| POST /auth/send-code | verification_codes |
| POST /auth/login | users, refresh_tokens |
| POST /auth/refresh | refresh_tokens |
| GET /auth/me | users |
| PUT /auth/profile | users |
| POST /auth/certification | certifications |
| POST /auth/risk-assessment | risk_assessments, users |
| GET /categories | categories |
| GET /posts | posts, users, categories |
| GET /posts/{id} | posts, users, categories, attachments, likes, favorites |
| POST /posts | posts, post_tags, attachments |
| PUT /posts/{id} | posts, post_tags, attachments |
| DELETE /posts/{id} | posts (级联删除评论、附件等) |
| POST /posts/{id}/vote | vote_options, vote_records |
| GET /posts/{id}/comments | comments, users, likes |
| POST /posts/{id}/comments | comments |
| POST /posts/{id}/like | likes, posts (like_count) / comments (like_count) |
| POST /posts/{id}/collect | favorites, favorite_folders, posts (collect_count) |
| POST /posts/{id}/share | shares, posts (share_count) |
| GET /users/me/collections | favorites, favorite_folders, posts |
| POST /users/{id}/follow | follows, users (counters) |
| GET /users/{id}/followers | follows, users |
| GET /users/{id}/following | follows, users |
| PUT /users/me/starred | starred_users |
| POST /groups | groups, group_members |
| GET /groups | groups, group_members |
| POST /groups/{id}/join | group_members |
| POST /groups/{id}/members/approve | group_members |
| GET /messages | messages |
| POST /messages | messages |
| GET /feed | posts, follows, users |
| GET /hot | posts (按 last_activity_at 排序) |
| GET /search | posts (FULLTEXT), users |
| GET /search/suggestions | posts, users |
| GET /admin/review-queue | posts, comments (status='reviewing') |
| POST /admin/review-queue/{id}/review | review_logs, posts/comments |
| POST /report | reports |
| GET /admin/users | users |
| POST /admin/users/{id}/ban | ban_records, users |
| GET /admin/stats/overview | daily_stats (或实时 COUNT) |
| GET /admin/stats/trend | daily_stats (或实时聚合) |
| POST /admin/categories | categories |
| PUT /admin/categories/{id} | categories |
| DELETE /admin/categories/{id} | categories |
| GET /health | 无数据库依赖 |

---

## 九、完整建表 SQL

完整的 `CREATE TABLE` 语句（按依赖顺序排列）存放于 `database/schema.sql` 文件中。

执行顺序：
1. `database/schema.sql` — 建库 + 建表
2. `database/seed.sql` — 种子数据

---

*本文档由陶畅编写，基于项目架构文档、OpenAPI 规范和用户故事设计。后续表结构变更需同步更新本文档。*

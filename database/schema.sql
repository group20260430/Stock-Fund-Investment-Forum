-- ============================================================================
-- 股票基金投资论坛 (Stock Fund Investment Forum)
-- 数据库建表脚本 v2.0
--
-- 数据库: MySQL 8.0+
-- 字符集: utf8mb4 / utf8mb4_unicode_ci
-- 引擎:   InnoDB
-- 设计:   陶畅 (后端开发 A)
-- 日期:   2026-06-19
--
-- 执行顺序: 本文件按依赖关系排序，可直接执行
-- ============================================================================

CREATE DATABASE IF NOT EXISTS stock_fund_forum
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE stock_fund_forum;

-- ============================================================================
-- 模块1: 用户系统 (User System) — 5 tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. users — 用户账户表 (核心表)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '用户ID',
  phone           VARCHAR(11)    NOT NULL UNIQUE              COMMENT '手机号，11位数字',
  email           VARCHAR(120)   NULL                         COMMENT '邮箱地址',
  password_hash   VARCHAR(255)   NOT NULL                     COMMENT 'bcrypt密码哈希',
  nickname        VARCHAR(50)    NOT NULL                     COMMENT '用户昵称，2~20字符',
  avatar_url      VARCHAR(500)   NULL                         COMMENT '头像URL',
  bio             VARCHAR(500)   NULL                         COMMENT '个人简介',
  role            ENUM('user','moderator','admin')
                                  NOT NULL DEFAULT 'user'     COMMENT '角色',
  auth_level      ENUM('none','basic','verified','professional')
                                  NOT NULL DEFAULT 'none'     COMMENT '认证等级',
  risk_level      ENUM('conservative','moderate','aggressive')
                                  NULL                         COMMENT '风险偏好',
  status          ENUM('active','disabled')
                                  NOT NULL DEFAULT 'active'    COMMENT '账户状态',
  register_type   ENUM('phone','email','wechat','weibo')
                                  NOT NULL DEFAULT 'phone'    COMMENT '注册方式',
  investment_tags JSON            NULL                         COMMENT '投资标签',
  follow_markets  JSON            NULL                         COMMENT '关注市场',
  is_professional TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否专业认证',
  ban_expires_at  TIMESTAMP       NULL                         COMMENT '封禁到期时间',
  banned_reason   VARCHAR(255)    NULL                         COMMENT '封禁原因',
  followers_count INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '粉丝数(冗余)',
  following_count INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '关注数(冗余)',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
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

-- ----------------------------------------------------------------------------
-- 2. verification_codes — 短信验证码表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verification_codes (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  phone           VARCHAR(11)    NOT NULL                     COMMENT '手机号',
  code            VARCHAR(10)    NOT NULL                     COMMENT '6位验证码',
  type            ENUM('register','login','reset_password')
                                  NOT NULL                     COMMENT '验证码类型',
  expires_at      TIMESTAMP      NOT NULL                     COMMENT '过期时间',
  is_used         TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否已使用',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',

  INDEX idx_vc_phone_type        (phone, type),
  INDEX idx_vc_phone_code        (phone, code),
  INDEX idx_vc_expires           (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='短信验证码表';

-- ----------------------------------------------------------------------------
-- 3. certifications — 实名认证记录表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS certifications (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '认证记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '申请人用户ID',
  real_name       VARCHAR(255)    NOT NULL                     COMMENT '真实姓名(AES加密)',
  id_number       VARCHAR(255)    NOT NULL                     COMMENT '身份证号(AES加密)',
  id_card_front   VARCHAR(500)    NOT NULL                     COMMENT '身份证正面照片URL',
  id_card_back    VARCHAR(500)    NOT NULL                     COMMENT '身份证反面照片URL',
  status          ENUM('pending','approved','rejected')
                                  NOT NULL DEFAULT 'pending'   COMMENT '审核状态',
  reviewer_id     BIGINT UNSIGNED NULL                         COMMENT '审核人ID',
  review_comment  VARCHAR(500)    NULL                         COMMENT '审核意见',
  reviewed_at     TIMESTAMP       NULL                         COMMENT '审核时间',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',

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

-- ----------------------------------------------------------------------------
-- 4. risk_assessments — 风险评估记录表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_assessments (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '评估记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  answers         JSON            NOT NULL                     COMMENT '答案数组',
  total_questions INT             NOT NULL DEFAULT 15          COMMENT '题目总数',
  score           INT             NOT NULL                     COMMENT '风险评分',
  max_score       INT             NOT NULL DEFAULT 100         COMMENT '满分值',
  risk_level      ENUM('conservative','moderate','aggressive')
                                  NOT NULL                     COMMENT '评估结果',
  suggestion      TEXT            NULL                         COMMENT '系统建议文本',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评估时间',

  CONSTRAINT fk_risk_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_risk_user (user_id),
  INDEX idx_risk_level(risk_level),
  INDEX idx_risk_time (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='风险评估记录表';

-- ----------------------------------------------------------------------------
-- 5. refresh_tokens — JWT刷新令牌表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '令牌记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '所属用户ID',
  token_hash      VARCHAR(255)    NOT NULL                     COMMENT 'Token SHA-256哈希',
  expires_at      TIMESTAMP       NOT NULL                     COMMENT '过期时间',
  is_revoked      TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否已撤销',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '签发时间',

  CONSTRAINT fk_rt_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_rt_hash   (token_hash),
  INDEX idx_rt_user          (user_id),
  INDEX idx_rt_expires       (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='JWT刷新令牌表';


-- ============================================================================
-- 模块2: 内容系统 (Content System) — 11 tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 6. categories — 内容板块表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '板块ID',
  name            VARCHAR(50)    NOT NULL UNIQUE              COMMENT '板块名称',
  description     VARCHAR(255)   NULL                         COMMENT '板块描述',
  sort_order      INT            NOT NULL DEFAULT 0            COMMENT '排序序号',
  is_active       TINYINT(1)    NOT NULL DEFAULT 1            COMMENT '是否启用',
  post_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '帖子数(冗余)',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

  INDEX idx_cat_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='内容板块表';

-- ----------------------------------------------------------------------------
-- 7. posts — 帖子表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '帖子ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '作者用户ID',
  category_id     BIGINT UNSIGNED NOT NULL                    COMMENT '所属板块ID',
  title           VARCHAR(120)    NOT NULL                     COMMENT '帖子标题',
  content         TEXT            NOT NULL                     COMMENT '帖子正文',
  post_type       ENUM('normal','long_article','poll','moment')
                                  NOT NULL DEFAULT 'normal'    COMMENT '帖子类型',
  status          ENUM('draft','published','reviewing','rejected')
                                  NOT NULL DEFAULT 'published' COMMENT '状态',
  is_elite        TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否精华帖',
  tags            JSON            NULL                         COMMENT '标签数组',
  view_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '浏览次数',
  like_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '点赞数(冗余)',
  comment_count   INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '评论数(冗余)',
  collect_count   INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '收藏数(冗余)',
  share_count     INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '转发数(冗余)',
  last_activity_at TIMESTAMP     NULL                         COMMENT '最后活动时间',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
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

-- ----------------------------------------------------------------------------
-- 8. comments — 评论表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '评论ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '所属帖子ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '评论者用户ID',
  parent_id       BIGINT UNSIGNED NULL                         COMMENT '父评论ID(一级评论为NULL)',
  reply_to_id     BIGINT UNSIGNED NULL                         COMMENT '被回复评论ID(@提及)',
  content         TEXT            NOT NULL                     COMMENT '评论正文',
  like_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '点赞数(冗余)',
  status          ENUM('published','reviewing','rejected')
                                  NOT NULL DEFAULT 'published' COMMENT '状态',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
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

-- ----------------------------------------------------------------------------
-- 9. post_tags — 帖子标签关联表
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 10. attachments — 文件附件表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attachments (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '附件ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '所属帖子ID',
  file_name       VARCHAR(255)    NOT NULL                     COMMENT '原始文件名',
  file_url        VARCHAR(500)    NOT NULL                     COMMENT '文件存储URL',
  file_size       INT UNSIGNED   NOT NULL                     COMMENT '文件大小(字节)',
  file_type       VARCHAR(50)     NOT NULL                     COMMENT 'MIME类型',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',

  CONSTRAINT fk_att_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  INDEX idx_att_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='文件附件表';

-- ----------------------------------------------------------------------------
-- 11. likes — 点赞记录表(统一帖子与评论)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS likes (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '点赞记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '点赞用户ID',
  target_type     ENUM('post','comment')
                                  NOT NULL                     COMMENT '目标类型',
  target_id       BIGINT UNSIGNED NOT NULL                    COMMENT '目标ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',

  CONSTRAINT fk_likes_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_likes_unique  (user_id, target_type, target_id),
  INDEX idx_likes_target         (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='点赞记录表';

-- ----------------------------------------------------------------------------
-- 12. favorite_folders — 收藏文件夹表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favorite_folders (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '文件夹ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  name            VARCHAR(50)     NOT NULL DEFAULT '默认收藏夹' COMMENT '文件夹名称',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

  CONSTRAINT fk_ff_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_ff_user_name (user_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='收藏文件夹表';

-- ----------------------------------------------------------------------------
-- 13. favorites — 收藏记录表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favorites (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '收藏记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '帖子ID',
  folder_id       BIGINT UNSIGNED NOT NULL                    COMMENT '所属收藏夹ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',

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

-- ----------------------------------------------------------------------------
-- 14. shares — 转发记录表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shares (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '转发记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '转发用户ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '被转发帖子ID',
  share_type      ENUM('timeline','message','group')
                                  NOT NULL                     COMMENT '转发类型',
  comment         VARCHAR(500)    NULL                         COMMENT '转发附言',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '转发时间',

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

-- ----------------------------------------------------------------------------
-- 15. vote_options — 投票选项表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vote_options (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '选项ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '投票帖子ID',
  label           VARCHAR(200)    NOT NULL                     COMMENT '选项文本',
  vote_count      INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '得票数(冗余)',
  sort_order      INT            NOT NULL DEFAULT 0            COMMENT '显示顺序',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

  CONSTRAINT fk_vo_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  INDEX idx_vo_post (post_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='投票选项表';

-- ----------------------------------------------------------------------------
-- 16. vote_records — 用户投票记录表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vote_records (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '投票记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '投票用户ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '投票帖子ID',
  option_id       BIGINT UNSIGNED NOT NULL                    COMMENT '选择的选项ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '投票时间',
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP  COMMENT '更改投票时间',

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


-- ============================================================================
-- 模块3: 社交系统 (Social System) — 5 tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 17. follows — 关注关系表 (保持原有结构)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS follows (
  follower_id     BIGINT UNSIGNED NOT NULL                    COMMENT '关注者用户ID',
  following_id    BIGINT UNSIGNED NOT NULL                    COMMENT '被关注者用户ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',

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

-- ----------------------------------------------------------------------------
-- 18. starred_users — 星标用户表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS starred_users (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  starred_user_id BIGINT UNSIGNED NOT NULL                    COMMENT '被星标的用户ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '设置时间',

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

-- ----------------------------------------------------------------------------
-- 19. groups — 投资群组表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `groups` (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '群组ID',
  name            VARCHAR(50)    NOT NULL UNIQUE              COMMENT '群组名称',
  description     VARCHAR(500)   NULL                         COMMENT '群组描述',
  avatar_url      VARCHAR(500)   NULL                         COMMENT '群组头像URL',
  visibility      ENUM('public','private')
                                  NOT NULL DEFAULT 'public'    COMMENT '可见性',
  need_approval   TINYINT(1)    NOT NULL DEFAULT 0            COMMENT '加入是否需要审批',
  creator_id      BIGINT UNSIGNED NOT NULL                    COMMENT '创建者用户ID',
  member_count    INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '成员数(冗余)',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
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

-- ----------------------------------------------------------------------------
-- 20. group_members — 群组成员表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_members (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '成员记录ID',
  group_id        BIGINT UNSIGNED NOT NULL                    COMMENT '群组ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  role            ENUM('owner','admin','member')
                                  NOT NULL DEFAULT 'member'    COMMENT '成员角色',
  status          ENUM('pending','approved','rejected')
                                  NOT NULL DEFAULT 'approved'  COMMENT '加入状态',
  joined_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',

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

-- ----------------------------------------------------------------------------
-- 20b. group_posts — 群组帖子关联表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_posts (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  group_id        BIGINT UNSIGNED NOT NULL                    COMMENT '群组ID',
  post_id         BIGINT UNSIGNED NOT NULL                    COMMENT '帖子ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关联时间',

  CONSTRAINT fk_gp_group
    FOREIGN KEY (group_id) REFERENCES `groups`(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_gp_post
    FOREIGN KEY (post_id) REFERENCES posts(id)
    ON DELETE CASCADE,

  UNIQUE INDEX idx_gp_unique (group_id, post_id),
  INDEX idx_gp_post           (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='群组帖子关联表';

-- ----------------------------------------------------------------------------
-- 21. messages — 私信/群聊消息表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '消息ID',
  sender_id       BIGINT UNSIGNED NOT NULL                    COMMENT '发送者用户ID',
  receiver_id     BIGINT UNSIGNED NULL                         COMMENT '接收者用户ID（群聊时为NULL）',
  group_id        BIGINT UNSIGNED NULL                         COMMENT '群组ID（私信时为NULL）',
  content         TEXT            NOT NULL                     COMMENT '消息正文',
  message_type    ENUM('text','image','file')
                                  NOT NULL DEFAULT 'text'      COMMENT '消息类型',
  attachment_url  VARCHAR(500)    NULL                         COMMENT '附件URL',
  is_read         TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否已读',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',

  CONSTRAINT fk_msg_sender
    FOREIGN KEY (sender_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_msg_receiver
    FOREIGN KEY (receiver_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_msg_group
    FOREIGN KEY (group_id) REFERENCES `groups`(id)
    ON DELETE CASCADE,

  INDEX idx_msg_conversation (sender_id, receiver_id, created_at),
  INDEX idx_msg_receiver_unread (receiver_id, is_read, created_at),
  INDEX idx_msg_group           (group_id, created_at),
  INDEX idx_msg_created         (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='私信/群聊消息表';

-- ----------------------------------------------------------------------------
-- 22. notifications — 通知表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '通知ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '接收用户ID',
  type            ENUM('follow','group_invite','group_join_request','group_approved','group_rejected','new_message','new_group_message','mention','system')
                                  NOT NULL                    COMMENT '通知类型',
  title           VARCHAR(200)    NOT NULL                    COMMENT '通知标题',
  content         VARCHAR(500)    NOT NULL                    COMMENT '通知内容',
  is_read         TINYINT(1)     NOT NULL DEFAULT 0            COMMENT '是否已读',
  target_type     VARCHAR(20)     NULL                         COMMENT '关联目标类型',
  target_id       BIGINT UNSIGNED NULL                         COMMENT '关联目标ID',
  sender_id       BIGINT UNSIGNED NULL                         COMMENT '触发者用户ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '通知时间',

  CONSTRAINT fk_notif_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_notif_sender
    FOREIGN KEY (sender_id) REFERENCES users(id)
    ON DELETE SET NULL,

  INDEX idx_notif_user_unread (user_id, is_read, created_at),
  INDEX idx_notif_type        (type),
  INDEX idx_notif_created     (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='通知表';


-- ============================================================================
-- 模块4: 管理运营系统 (Admin & Operations) — 4 tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 22. reports — 举报记录表
-- ----------------------------------------------------------------------------
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
  handler_id      BIGINT UNSIGNED NULL                         COMMENT '处理人ID',
  handle_comment  VARCHAR(500)    NULL                         COMMENT '处理意见',
  handled_at      TIMESTAMP       NULL                         COMMENT '处理时间',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '举报时间',

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

-- ----------------------------------------------------------------------------
-- 23. review_logs — 审核日志表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_logs (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '日志ID',
  target_type     ENUM('post','comment')
                                  NOT NULL                     COMMENT '审核目标类型',
  target_id       BIGINT UNSIGNED NOT NULL                    COMMENT '审核目标ID',
  reviewer_id     BIGINT UNSIGNED NOT NULL                    COMMENT '审核人ID',
  action          ENUM('approve','reject','edit')
                                  NOT NULL                     COMMENT '审核操作',
  comment         VARCHAR(500)    NULL                         COMMENT '审核意见',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '审核时间',

  CONSTRAINT fk_rl_reviewer
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_rl_target     (target_type, target_id),
  INDEX idx_rl_reviewer   (reviewer_id, created_at),
  INDEX idx_rl_action     (action, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='审核日志表';

-- ----------------------------------------------------------------------------
-- 24. ban_records — 封禁记录表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ban_records (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '记录ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '被封禁用户ID',
  admin_id        BIGINT UNSIGNED NOT NULL                    COMMENT '操作管理员ID',
  action          ENUM('ban','unban')
                                  NOT NULL                     COMMENT '操作类型',
  reason          VARCHAR(500)    NULL                         COMMENT '封禁/解封原因',
  duration_hours  INT UNSIGNED   NULL                         COMMENT '封禁时长(小时), NULL=永久',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',

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

-- ----------------------------------------------------------------------------
-- 25. sensitive_words — 敏感词库表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sensitive_words (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '词条ID',
  word            VARCHAR(100)    NOT NULL UNIQUE              COMMENT '敏感词',
  level           ENUM('block','review','warn')
                                  NOT NULL DEFAULT 'review'    COMMENT '触发级别',
  category        VARCHAR(50)     NULL                         COMMENT '词条分类',
  is_active       TINYINT(1)     NOT NULL DEFAULT 1            COMMENT '是否启用',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',

  INDEX idx_sw_level (level, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='敏感词库表';


-- ============================================================================
-- 模块5: 统计与日志系统 (Statistics & Logging) — 1 table
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 26. daily_stats — 每日统计表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_stats (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '统计ID',
  stat_date       DATE            NOT NULL UNIQUE              COMMENT '统计日期',
  dau             INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '日活跃用户数',
  new_users       INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增注册数',
  total_posts     INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增帖子数',
  total_comments  INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增评论数',
  total_likes     INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日点赞数',
  total_shares    INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日转发数',
  reports_count   INT UNSIGNED   NOT NULL DEFAULT 0            COMMENT '当日新增举报数',
  created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  updated_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP   COMMENT '记录更新时间',

  INDEX idx_ds_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='每日统计表';

-- ----------------------------------------------------------------------------
-- 27. user_activity_log — 用户活动日志表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_activity_log (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '日志ID',
  user_id         BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
  activity_type   ENUM('login','post','comment','like','follow','share','vote')
                                  NOT NULL                     COMMENT '活动类型',
  target_type     VARCHAR(20)     NULL                         COMMENT '活动目标类型',
  target_id       BIGINT UNSIGNED NULL                         COMMENT '活动目标ID',
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '活动时间',

  CONSTRAINT fk_ual_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  INDEX idx_ual_user_date    (user_id, created_at),
  INDEX idx_ual_date_type    (created_at, activity_type),
  INDEX idx_ual_activity     (activity_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户活动日志表';

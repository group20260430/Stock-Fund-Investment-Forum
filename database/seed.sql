-- ============================================================================
-- 股票基金投资论坛 (Stock Fund Investment Forum)
-- 种子数据脚本 v2.0
--
-- 在 schema.sql 执行后运行本脚本
-- ============================================================================

USE stock_fund_forum;

-- ============================================================================
-- 1. 板块分类数据
-- ============================================================================
INSERT INTO categories (name, description, sort_order) VALUES
  ('股票市场', 'A股、港股、美股等股票市场讨论', 10),
  ('基金投资', '指数基金、主动基金、资产配置讨论', 20),
  ('问答求助', '新手问题、投资知识和工具求助', 30),
  ('投资策略', '价值投资、量化投资和宏观策略讨论', 40)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  sort_order = VALUES(sort_order);

-- ============================================================================
-- 2. 测试用户数据（密码均为 Test@123456 的 bcrypt 哈希，仅用于本地开发）
--    bcrypt($2b$12$ 需替换为实际哈希值)
-- ============================================================================
INSERT INTO users (phone, email, password_hash, nickname, bio, role, auth_level, investment_tags, follow_markets)
VALUES
  ('13800000001', 'admin@example.com',  'replace_with_real_bcrypt_hash', '系统管理员', '论坛系统管理员', 'admin', 'professional', '["系统管理"]', '["A股","港股","美股"]'),
  ('13800000002', 'mod@example.com',    'replace_with_real_bcrypt_hash', '版主小王',     '股票市场版主',     'moderator', 'verified', '["价值投资","技术分析"]', '["A股"]'),
  ('13800000003', 'user1@example.com',  'replace_with_real_bcrypt_hash', '投资达人小明', '价值投资者，专注消费行业', 'user', 'basic', '["价值投资","消费","A股"]', '["A股","港股"]'),
  ('13800000004', 'user2@example.com',  'replace_with_real_bcrypt_hash', '基金观察者',   '关注基金配置与长期投资', 'user', 'basic', '["基金定投","资产配置"]', '["基金"]')
ON DUPLICATE KEY UPDATE
  bio = VALUES(bio);

-- ============================================================================
-- 3. 示例帖子数据
-- ============================================================================
INSERT INTO posts (user_id, category_id, title, content, post_type, status, like_count, comment_count, tags)
SELECT u.id, c.id, 'A股市场今日走势分析',
       '## 今日大盘回顾\n\n今日A股三大指数震荡走高，沪指收涨0.8%...\n\n### 热点板块\n- 新能源板块整体走强\n- 消费电子板块回调\n\n> 投资有风险，入市需谨慎。',
       'long_article', 'published', 12, 3,
       '["A股","盘面分析","新能源"]'
FROM users u, categories c
WHERE u.phone = '13800000003'
  AND c.name = '股票市场'
  AND NOT EXISTS (
    SELECT 1 FROM posts p WHERE p.title = 'A股市场今日走势分析' AND p.user_id = u.id
  );

INSERT INTO posts (user_id, category_id, title, content, post_type, status, like_count, comment_count, tags)
SELECT u.id, c.id, '指数基金长期配置思路分享',
       '## 我的基金配置策略\n\n核心-卫星策略：\n1. **核心仓位(70%)**：沪深300+中证500指数基金\n2. **卫星仓位(30%)**：行业主题基金\n\n长期年化收益目标：8-10%',
       'long_article', 'published', 21, 7,
       '["基金","资产配置","定投"]'
FROM users u, categories c
WHERE u.phone = '13800000004'
  AND c.name = '基金投资'
  AND NOT EXISTS (
    SELECT 1 FROM posts p WHERE p.title = '指数基金长期配置思路分享' AND p.user_id = u.id
  );

INSERT INTO posts (user_id, category_id, title, content, post_type, status, like_count, comment_count, tags)
SELECT u.id, c.id, '大家看好下半年的A股吗？',
       '做个市场情绪调查，看看大家对下半年行情的看法。',
       'poll', 'published', 5, 2,
       '["市场情绪","投票"]'
FROM users u, categories c
WHERE u.phone = '13800000003'
  AND c.name = '股票市场'
  AND NOT EXISTS (
    SELECT 1 FROM posts p WHERE p.title = '大家看好下半年的A股吗？' AND p.user_id = u.id
  );

-- ============================================================================
-- 4. 示例投票选项（为上面的 poll 类型帖子）
-- ============================================================================
INSERT INTO vote_options (post_id, label, sort_order)
SELECT p.id, '非常看好，牛市可期', 1
FROM posts p WHERE p.title = '大家看好下半年的A股吗？'
  AND NOT EXISTS (SELECT 1 FROM vote_options vo WHERE vo.post_id = p.id AND vo.label = '非常看好，牛市可期');

INSERT INTO vote_options (post_id, label, sort_order)
SELECT p.id, '谨慎乐观，震荡向上', 2
FROM posts p WHERE p.title = '大家看好下半年的A股吗？'
  AND NOT EXISTS (SELECT 1 FROM vote_options vo WHERE vo.post_id = p.id AND vo.label = '谨慎乐观，震荡向上');

INSERT INTO vote_options (post_id, label, sort_order)
SELECT p.id, '不太乐观，有调整压力', 3
FROM posts p WHERE p.title = '大家看好下半年的A股吗？'
  AND NOT EXISTS (SELECT 1 FROM vote_options vo WHERE vo.post_id = p.id AND vo.label = '不太乐观，有调整压力');

-- ============================================================================
-- 5. 示例评论数据
-- ============================================================================
INSERT INTO comments (post_id, user_id, content, like_count)
SELECT p.id, u.id, '分析得很透彻，学习了！', 5
FROM posts p, users u
WHERE p.title = 'A股市场今日走势分析'
  AND u.phone = '13800000004'
  AND NOT EXISTS (
    SELECT 1 FROM comments c WHERE c.post_id = p.id AND c.user_id = u.id AND c.content = '分析得很透彻，学习了！'
  );

INSERT INTO comments (post_id, user_id, content, like_count)
SELECT p.id, u.id, '请问沪深300现在适合定投吗？', 2
FROM posts p, users u
WHERE p.title = '指数基金长期配置思路分享'
  AND u.phone = '13800000003'
  AND NOT EXISTS (
    SELECT 1 FROM comments c WHERE c.post_id = p.id AND c.user_id = u.id AND c.content = '请问沪深300现在适合定投吗？'
  );

-- ============================================================================
-- 6. 关注关系
-- ============================================================================
INSERT INTO follows (follower_id, following_id)
SELECT u1.id, u2.id
FROM users u1, users u2
WHERE u1.phone = '13800000003' AND u2.phone = '13800000004'
  AND NOT EXISTS (SELECT 1 FROM follows f WHERE f.follower_id = u1.id AND f.following_id = u2.id);

INSERT INTO follows (follower_id, following_id)
SELECT u1.id, u2.id
FROM users u1, users u2
WHERE u1.phone = '13800000004' AND u2.phone = '13800000003'
  AND NOT EXISTS (SELECT 1 FROM follows f WHERE f.follower_id = u1.id AND f.following_id = u2.id);

-- ============================================================================
-- 7. 敏感词初始化
-- ============================================================================
INSERT INTO sensitive_words (word, level, category) VALUES
  ('非法集资',     'block',   '金融违规'),
  ('荐股',         'review',  '金融合规'),
  ('内幕消息',     'block',   '金融违规'),
  ('保证收益',     'review',  '金融合规'),
  ('稳赚不赔',     'review',  '金融合规'),
  ('代客理财',     'block',   '金融违规'),
  ('涨停预测',     'review',  '金融合规'),
  ('暴力拉升',     'warn',    '金融合规'),
  ('必涨',         'review',  '金融合规')
ON DUPLICATE KEY UPDATE
  level = VALUES(level),
  category = VALUES(category);

-- ============================================================================
-- 8. 收藏文件夹和收藏示例
-- ============================================================================
INSERT INTO favorite_folders (user_id, name)
SELECT u.id, '基金分析'
FROM users u
WHERE u.phone = '13800000004'
  AND NOT EXISTS (SELECT 1 FROM favorite_folders ff WHERE ff.user_id = u.id AND ff.name = '基金分析');

INSERT INTO favorite_folders (user_id, name)
SELECT u.id, '股票研究'
FROM users u
WHERE u.phone = '13800000003'
  AND NOT EXISTS (SELECT 1 FROM favorite_folders ff WHERE ff.user_id = u.id AND ff.name = '股票研究');

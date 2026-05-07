USE stock_fund_forum;

INSERT INTO categories (name, description, sort_order) VALUES
  ('股票市场', 'A股、港股、美股等股票市场讨论', 10),
  ('基金投资', '指数基金、主动基金、资产配置讨论', 20),
  ('问答求助', '新手问题、投资知识和工具求助', 30),
  ('投资策略', '价值投资、量化投资和宏观策略讨论', 40)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  sort_order = VALUES(sort_order);

INSERT INTO users (username, email, password_hash, bio) VALUES
  ('system_user', 'system@example.com', 'replace_with_real_hash', '系统初始化用户'),
  ('fund_watcher', 'fund@example.com', 'replace_with_real_hash', '关注基金配置与长期投资')
ON DUPLICATE KEY UPDATE
  bio = VALUES(bio);

INSERT INTO posts (user_id, category_id, title, content, like_count, comment_count)
SELECT u.id, c.id, 'A股市场今日讨论', '这里是论坛初始化示例帖，后续可替换为真实发帖流程。', 12, 3
FROM users u, categories c
WHERE u.username = 'system_user'
  AND c.name = '股票市场'
  AND NOT EXISTS (
    SELECT 1 FROM posts p WHERE p.title = 'A股市场今日讨论' AND p.user_id = u.id
  );

INSERT INTO posts (user_id, category_id, title, content, like_count, comment_count)
SELECT u.id, c.id, '指数基金长期配置思路', '这里是基金投资板块的初始化示例帖。', 21, 7
FROM users u, categories c
WHERE u.username = 'fund_watcher'
  AND c.name = '基金投资'
  AND NOT EXISTS (
    SELECT 1 FROM posts p WHERE p.title = '指数基金长期配置思路' AND p.user_id = u.id
  );

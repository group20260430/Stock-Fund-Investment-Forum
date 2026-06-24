"""修复数据库中的板块数据"""
import sqlite3

conn = sqlite3.connect('stock_fund_forum.db')

# 检查现有板块和表结构
print("=== categories表结构 ===")
cols = conn.execute("PRAGMA table_info(categories)").fetchall()
for c in cols:
    print(c)

print("\n=== 当前板块 ===")
rows = conn.execute("SELECT id, name FROM categories ORDER BY id").fetchall()
print(rows)

# 直接插入（不使用OR IGNORE，先检查是否存在）
for name, desc, sort in [('A股', 'A股市场讨论', 12), ('港股', '港股市场讨论', 13)]:
    exists = conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()
    if exists:
        print(f"{name} 已存在 id={exists[0]}")
    else:
        conn.execute("INSERT INTO categories (name, description, sort_order, is_active, post_count) VALUES (?, ?, ?, 1, 0)", (name, desc, sort))
        print(f"插入 {name}")

conn.commit()

rows = conn.execute("SELECT id, name FROM categories ORDER BY id").fetchall()
print("\n修复后板块:", rows)

# 将帖子1（A股市场今日讨论）关联到A股板块
aogu = conn.execute("SELECT id FROM categories WHERE name='A股'").fetchone()
if aogu:
    conn.execute("UPDATE posts SET category_id=? WHERE id=1", (aogu[0],))
    conn.commit()
    print(f"\n帖子1已关联到A股(id={aogu[0]})")

posts = conn.execute('SELECT id, title, category_id FROM posts').fetchall()
print("\n帖子最终分布:")
for p in posts:
    print(f"  id={p[0]}, title={p[1]}, category_id={p[2]}")
conn.close()

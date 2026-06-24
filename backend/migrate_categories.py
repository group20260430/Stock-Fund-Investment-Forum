"""数据库迁移：为 categories 表添加 parent_id 字段，并建立层级关系"""
import sqlite3

conn = sqlite3.connect('stock_fund_forum.db')
conn.execute('PRAGMA foreign_keys=OFF')

# 1. 添加 parent_id 列
try:
    conn.execute("ALTER TABLE categories ADD COLUMN parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE")
    print("OK 添加 parent_id 列")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("OK parent_id 列已存在")
    else:
        raise

# 2. 建立层级
sections = {
    '市场讨论区': 10,
    '主题专区': 20,
    '问答求助区': 30,
}

for name, sort in sections.items():
    exists = conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO categories (name, description, sort_order, is_active, post_count) VALUES (?, ?, ?, 1, 0)",
            (name, '', sort)
        )
        print(f"OK 创建: {name}")

conn.commit()

# 3. 归类子板块
mapping = {
    '市场讨论区': ['A股', '港股', '美股', '期货'],
    '主题专区': ['价值投资', '量化投资', '基金研究', '新股/新债', '宏观策略'],
    '问答求助区': ['新手提问', '投资解惑'],
}

for section_name, children in mapping.items():
    section = conn.execute("SELECT id FROM categories WHERE name=?", (section_name,)).fetchone()
    if not section:
        continue
    sid = section[0]
    for child_name in children:
        child = conn.execute("SELECT id, parent_id FROM categories WHERE name=?", (child_name,)).fetchone()
        if child:
            if child[1] is None:
                conn.execute("UPDATE categories SET parent_id=? WHERE id=?", (sid, child[0]))
                print(f"  {child_name} -> {section_name}")
        else:
            conn.execute(
                "INSERT INTO categories (name, description, parent_id, sort_order, is_active, post_count) VALUES (?, ?, ?, 1, 1, 0)",
                (child_name, '', sid)
            )
            print(f"  OK 创建并归类: {child_name} -> {section_name}")

conn.commit()

# 4. 删除无用的公司研究区
cr = conn.execute("SELECT id, post_count FROM categories WHERE name='公司研究区'").fetchone()
if cr and cr[1] == 0:
    conn.execute("DELETE FROM categories WHERE id=?", (cr[0],))
    print("OK 删除 公司研究区")

conn.commit()

# 5. 验证
rows = conn.execute("""
    SELECT c.id, c.name, c.parent_id, p.name as parent_name
    FROM categories c
    LEFT JOIN categories p ON c.parent_id = p.id
    ORDER BY c.sort_order, c.id
""").fetchall()

print("\n最终结构:")
for r in rows:
    tag = f" (父: {r[3]})" if r[2] else " [顶级分区]"
    print(f"  id={r[0]}, {r[1]}{tag}")

conn.execute('PRAGMA foreign_keys=ON')
conn.close()

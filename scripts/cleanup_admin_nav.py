"""Remove inline admin-nav HTML and CSS from all admin page files."""
import re, os

admin_dir = r'C:\Users\hejiaxuan\Stock-Fund-Investment-Forum\frontend\src\views\admin'
files = [
    'ReviewQueue.vue', 'UserManagement.vue', 'ActivityLogs.vue',
    'HotTopics.vue', 'Engagement.vue', 'Dashboard.vue', 'Categories.vue',
]

html_pattern = re.compile(
    r'    <div class="admin-nav">\n'
    r'(?:      <router-link[^>]+>[^<]+</router-link>\n)+'
    r'    </div>\n\n'
)

for fname in files:
    path = os.path.join(admin_dir, fname)
    if not os.path.exists(path):
        print(f'{fname}: not found')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = html_pattern.sub('', content)
    
    # Remove admin-nav CSS rules
    lines = new_content.split('\n')
    filtered = []
    skip = False
    for line in lines:
        if '.admin-nav' in line and '{' in line:
            skip = True
            continue
        if skip:
            if '}' in line:
                skip = False
            continue
        if '.admin-nav__item' in line and '{' in line:
            skip = True
            continue
        if skip:
            if '}' in line:
                skip = False
            continue
        if '.admin-nav__item:hover' in line or '.admin-nav__item--active' in line:
            continue
        if '  .admin-nav__item ' in line:
            continue
        filtered.append(line)
    
    new_content = '\n'.join(filtered)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'{fname}: cleaned')
    else:
        print(f'{fname}: no changes')

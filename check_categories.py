import urllib.request, json
r = urllib.request.urlopen('http://localhost:8000/api/categories')
d = json.load(r)
print('分类数:', len(d['data']))
for c in d['data']:
    children = c.get('children', [])
    print(f'  [{c["id"]}] {c["name"]} ({len(children)}个子分类)')
    for child in children:
        print(f'    └ [{child["id"]}] {child["name"]}')

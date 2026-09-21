import re
import json

with open('mudafy_dump.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Search for /propiedades/ in text
slugs = set(re.findall(r'"/propiedades/([^"]+)"', text))
print('Unique /propiedades/ slugs:', len(slugs))
for s in list(slugs)[:10]:
    print('  ->', s)

# Search for property objects with prices
items = re.findall(r'(\{[^{}]*"price"[^{}]*\})', text)
print('Price blocks found:', len(items))
for it in items[:5]:
    print('  Snippet:', it[:120])

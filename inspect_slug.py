import re
import json

with open('mudafy_dump.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Find around the slug
slug = "3-de-febrero-1282-departamento-en-venta-082349"
pos = text.find(slug)
if pos != -1:
    print('Found slug at position:', pos)
    print('Context around slug:')
    print(text[max(0, pos - 300) : min(len(text), pos + 1000)])

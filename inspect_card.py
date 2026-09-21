with open('mudafy_dump.txt', 'r', encoding='utf-8') as f:
    text = f.read()

slug = "3-de-febrero-1282-departamento-en-venta-082349"
pos = text.find(slug)
if pos != -1:
    print(text[pos + 8000 : pos + 9500])

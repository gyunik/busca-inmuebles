import asyncio, httpx, re

async def check():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    async with httpx.AsyncClient(headers=headers, verify=False, follow_redirects=True) as client:
        r = await client.get('https://mudafy.com.ar/venta/propiedades/caba')
        with open('mudafy_dump.txt', 'w', encoding='utf-8') as out:
            out.write(r.text)
        print('Dumped', len(r.text), 'characters to mudafy_dump.txt')

asyncio.run(check())

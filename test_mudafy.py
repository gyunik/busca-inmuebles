import asyncio, httpx, re, json
from bs4 import BeautifulSoup

async def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    async with httpx.AsyncClient(headers=headers, verify=False, follow_redirects=True, timeout=15.0) as client:
        resp = await client.get('https://mudafy.com.ar/venta/propiedades/caba')
        soup = BeautifulSoup(resp.text, 'html.parser')
        for i, s in enumerate(soup.find_all('script')):
            txt = s.text
            if 'price' in txt and ('title' in txt or 'address' in txt or 'surface' in txt):
                print(f'Script {i} matches! Length: {len(txt)}')
                print(txt[:600])
                print('...')
                break

asyncio.run(main())

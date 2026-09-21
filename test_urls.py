import asyncio
import httpx
import re

async def test_urls():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    async with httpx.AsyncClient(headers=headers, verify=False, follow_redirects=True, timeout=10.0) as client:
        test_list = [
            'https://mudafy.com.ar/venta/propiedades/caba',
            'https://mudafy.com.ar/venta/departamentos/capital-federal',
            'https://mudafy.com.ar/venta/departamentos-en-capital-federal',
            'https://mudafy.com.ar/venta/casas-en-capital-federal',
            'https://mudafy.com.ar/venta/ph-en-capital-federal',
            'https://mudafy.com.ar/venta/propiedades/provincia-de-buenos-aires-gba-norte',
            'https://mudafy.com.ar/venta/propiedades/provincia-de-buenos-aires-gba-sur',
            'https://mudafy.com.ar/venta/propiedades/provincia-de-buenos-aires-gba-oeste'
        ]
        for u in test_list:
            r = await client.get(u)
            slugs = re.findall(r'href="(/propiedades/[a-zA-Z0-9\-]+)"', r.text)
            print(f'{u} -> status {r.status_code}, slugs found: {len(set(slugs))}')

if __name__ == '__main__':
    asyncio.run(test_urls())

import asyncio
from tools.web_reader import WebReader

def main():
    web_reader = WebReader()
    url = "https://www.youtube.com/watch?v=OThbpWnsdIQ&ab_channel=JulianGoldieSEO"
    
    print(f"\n正在读取网页: {url}")
    result = asyncio.run(web_reader.read_page(url))
    
    print(f"URL: {result['url']}")
    print(f"内容长度: {len(result['content'])} 字符")
    print(f"内容预览: {result['content'][:2000]}...")

if __name__ == '__main__':
    main()
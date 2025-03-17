import asyncio
from processors.text_processor import TextProcessor

async def main():
    processor = TextProcessor()
    text = """Привет, мир! 这是一个测试。
Программирование - это интересно! 让我们继续。

В этом тексте есть русские слова."""
    
    try:
        result = await processor.process_russian_text(text)
        print('\n原文:\n', text)
        print('\n处理后:\n', result)
    except Exception as e:
        print('错误:', str(e))

if __name__ == '__main__':
    asyncio.run(main())
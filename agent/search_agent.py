from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import signal

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from tools.google_search import GoogleSearch
from tools.web_reader import WebReader
from config.prompts.searcher_agent_prompt import get_deepseek_chat_prompt

class SearchAgent:
    """基于Deepseek Chat的智能搜索代理"""
    
    def __init__(self, system_prompt: str | None = None):
        """初始化搜索代理"""
        # 加载环境变量
        load_dotenv()
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.getenv('GEMINI_API_KEY')
        )
        
        # 初始化搜索工具
        self.google_search = GoogleSearch()
        self.web_reader = WebReader()
        
        # 设置系统提示词
        self.system_prompt = system_prompt or get_deepseek_chat_prompt()
        
        # 定义可用的工具
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_google",
                    "description": "使用Google搜索获取相关信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询字符串"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "返回结果数量，默认为5",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_webpage",
                    "description": "读取并解析网页内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "网页URL"
                            }
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    
    def search_google(self, query: str, num_results: int = 5) -> Dict:
        """执行Google搜索"""
        return self.google_search.search(query, num_results)
    
    async def read_webpage(self, url: str) -> Dict:
        """读取网页内容"""
        try:
            result = await self.web_reader.read_page(url)
            return {
                "status": "success",
                "url": url,
                "content": result
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "message": str(e)
            }
    
    async def process_query(self, query: str) -> Dict:
        """处理用户查询"""
        try:
            # 初始化消息列表
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": query}
            ]
            
            while True:
                # 调用Gemini模型
                response = self.client.chat.completions.create(
                    model="gemini-2.0-flash",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                # 处理模型响应
                message = response.choices[0].message
                print("模型响应:", message)
                
                # 如果模型有返回内容，先打印出来
                if message.content:
                    print("模型返回内容:", message.content)
                
                # 如果模型选择使用工具
                if message.tool_calls:
                    # 添加模型的工具调用消息到历史
                    messages.append(message)
                    
                    # 处理每个工具调用
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = eval(tool_call.function.arguments)
                        
                        # 执行相应的工具调用
                        if function_name == "search_google":
                            result = self.search_google(**function_args)
                        elif function_name == "read_webpage":
                            result = await self.read_webpage(**function_args)
                        else:
                            raise ValueError(f"未知的工具调用: {function_name}")
                        
                        # 添加工具响应消息，使用模型返回的tool_call_id
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result)
                        })
                        print(f"工具调用结果 (ID: {tool_call.id}):", result)
                else:
                    # 如果模型返回最终答案，退出循环
                    return {
                        "status": "success",
                        "answer": message.content
                    }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

def signal_handler(signum, frame):
    print("\n接收到终止信号，正在安全退出...")
    sys.exit(0)

async def main():
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建搜索代理实例
    agent = SearchAgent()
    
    try:
        # 测试查询
        query = "【检索任务描述】：用户想要了解关于「deep research」相关的信息，当前已知「deep research」是一类AI产品，openai、Google- Gemini、perplexity等公司都在研发相关产品。请你在本次搜索任务中完善deep research这类产品的定义和描述，清楚明白的定义什么是deep research，有什么功能，从而成为整个deep research研究报告的初始内容。特别注意，每次回复只允许调用一次工具，你应当结合每次工具调用后的结果再判断是否需要进一步使用工具"
        print(f"\n执行查询: {query}")
        
        result = await agent.process_query(query)
        
        if result["status"] == "success":
            if "tool_used" in result:
                print(f"\n使用工具: {result['tool_used']}")
                print("结果:", result["result"])
            else:
                print("\n直接回答:", result["answer"])
        else:
            print(f"\n错误: {result['message']}")
            
    except KeyboardInterrupt:
        print("\n用户中断，正在安全退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        sys.exit(1)
    finally:
        # 在这里可以添加任何需要的清理代码
        pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
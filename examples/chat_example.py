import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import json

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from tools.google_search_and_read import GoogleSearchTool
from tools.youtube_search import YouTubeSearchTool
from tools.zhipu_search import ZhipuSearchTool
from config.prompts import SYSTEM_PROMPTS

# 加载环境变量
load_dotenv()

def main(system_prompt_key="default"):
    # 获取system prompt
    system_prompt = SYSTEM_PROMPTS.get(system_prompt_key, SYSTEM_PROMPTS["default"])
    
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    # 初始化搜索工具
    google_search_tool = GoogleSearchTool()
    youtube_search_tool = YouTubeSearchTool()
    zhipu_search_tool = ZhipuSearchTool()
    
    # 定义可用的函数
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_google",
                "description": "使用 Google 搜索全球信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_youtube",
                "description": "搜索 YouTube 视频",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_zhipu",
                "description": "使用智谱搜索中文内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    # 初始化对话历史，加入system prompt
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    print("\n系统已启动，使用的角色模板:", system_prompt_key)
    print(messages)
    while True:
        # 获取用户输入
        user_input = input("\nUser: ")
        if user_input.lower() == 'quit':
            break
            
        # 添加用户消息到历史
        messages.append({"role": "user", "content": user_input})
        
        try:
            # 获取模型响应
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=8192,
                messages=messages,
                tools=tools
            )
            
            assistant_message = response.choices[0].message
            print("\nModel (Initial Response)>")
            print(f"Content: {assistant_message.content}")
            
            # 处理函数调用
            if assistant_message.tool_calls:
                print("\n所有工具调用:")
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n- 函数: {function_name}")
                    print(f"  参数: {args}")
                
                # 添加用户确认步骤
                confirmation = input("\n是否执行以上工具调用？(y/n): ")
                if confirmation.lower() != 'y':
                    print("已取消工具调用")
                    continue
                
                messages.append(assistant_message)
                
                # 处理每个工具调用
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n执行工具调用:")
                    print(f"- 函数: {function_name}")
                    print(f"  参数: {args}")
                    
                    # 执行工具调用
                    if function_name == "search_google":
                        result = google_search_tool.search(args["query"])
                    elif function_name == "search_youtube":
                        result = youtube_search_tool.search(args["query"])
                    elif function_name == "search_zhipu":
                        result = zhipu_search_tool.search(args["query"])
                    
                    print(f"\n工具调用结果:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                        
                    # 添加工具响应到消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # 获取最终响应
                final_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages
                )
                assistant_message = final_response.choices[0].message
                print("\nModel (Final Response)>")
                print(f"Content: {assistant_message.content}")
                messages.append(assistant_message)
            else:
                messages.append(assistant_message)
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue

if __name__ == "__main__":
    # 可以通过命令行参数或环境变量来选择不同的system prompt
    prompt_key = os.getenv("CHAT_PROMPT_KEY", "default")
    main(prompt_key) 
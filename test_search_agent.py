"""测试SearchAgent的功能

验证搜索任务处理、信息整合和文档保存的完整流程
"""

import os
import asyncio
from agent.search_agent import SearchAgent

async def test_search_agent():
    """测试SearchAgent的完整工作流程"""
    # 创建一个测试任务ID
    task_id = "test_search_task"
    
    # 创建任务目录
    task_dir = os.path.join(os.path.dirname(__file__), "tasks", task_id, "documents")
    os.makedirs(task_dir, exist_ok=True)
    
    # 初始化SearchAgent实例
    agent = SearchAgent(task_id)
    
    # 模拟一个搜索任务描述
    task_description = """
    当前整体研究任务是：**综合了解 "deep research" 同类型的产品，关注功能，以及这些产品之间的对比评测。**

    本次Search Agent的任务是：**在信息收集阶段，搜索并整理 "deep research" 同类型产品的列表。**

    请使用Google Search搜索以下关键词，并将结果整理成Markdown文档：
    * "deep research alternatives"
    * "AI research tools"

    请重点关注以下方面：
    * 产品名称
    * 产品定位
    * 核心功能

    请将文档保存为'deep_research_competitors.md'。
    """
    
    try:
        # 执行搜索任务并获取结果
        print("\n🔍 开始执行搜索任务...")
        print(f"📝 任务描述:\n{task_description}\n")
        
        result = await agent.process_search_task(task_description)
        
        # 打印搜索过程中的模型输出
        for message in agent.chat_history:
            if message["role"] == "assistant":
                print(f"\n🤖 模型输出:\n{message['content']}\n")
            elif message["role"] == "user" and "Quick Search Results" in message["content"]:
                print(f"🔎 {message['content']}\n")
            elif message["role"] == "user" and "Webpage Content" in message["content"]:
                print(f"📄 {message['content']}\n")
        
        # 验证结果
        assert result["status"] == "success", "搜索任务执行失败"
        assert "source" in result, "结果中缺少source字段"
        assert result["source"] == "search_agent", "source字段值不正确"
        
        # 验证文档是否已保存
        task_dir = os.path.join(os.path.dirname(__file__), "tasks", task_id, "documents")
        doc_path = os.path.join(task_dir, "deep_research_competitors.md")
        assert os.path.exists(doc_path), "文档未成功保存"
        
        print("✅ 测试通过：SearchAgent功能验证成功")
        print(f"📝 生成的文档路径：{doc_path}")
        
    except Exception as e:
        print(f"❌ 测试失败：{str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_search_agent())
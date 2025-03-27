"""文档名称处理器模块，负责从任务描述中提取合适的文档名称"""

import os
from typing import Optional
from openai import AsyncOpenAI

class DocNameProcessor:
    """基于Gemini模型的文档名称处理器类"""
    
    def __init__(self):
        """初始化文档名称处理器，配置Gemini API客户端"""
        self.client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY'),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    
    async def extract_doc_name(self, task_description: str) -> str:
        """从任务描述中提取合适的文档名称
        
        Args:
            task_description: 任务描述文本
            
        Returns:
            str: 提取的文档名称
        """
        response = await self.client.chat.completions.create(
            model="gemini-2.0-flash-lite",
            messages=[
                {"role": "system", "content": """
                    请你充当一个文档名称提取器。你的任务是从一段文本中提取出文档名称。文档名称通常会出现在 '请将文档保存为' 这句话的后面，并且用单引号 `''` 包裹。 如果提取出的文档名称包含文件路径，请只返回最后的文件名，不包含路径。

                    示例：
                    ```
                    输入：
                    当前整体研究任务是：**综合了解 "deep research" 同类型的产品，关注功能，以及这些产品之间的对比评测，目的是撰写竞品分析文档。**

                    本次 Search Agent 的任务是：**在信息收集阶段，搜索并整理 "deep research" 同类型产品的列表。**

                    请使用 Google Search 搜索以下关键词，并将结果整理成 Markdown 文档：

                    *   "deep research alternatives"
                    *   "AI research tools"
                    *   "AI powered research platforms"
                    *   "best AI research assistants"
                    *   "competitive analysis tools AI"

                    请重点关注以下方面：

                    *   产品名称
                    *   产品所属公司
                    *   产品定位 (例如，主要面向学术研究、市场研究、金融分析等)
                    *   产品是否具有 "deep research" 的类似功能 (例如，自动信息收集、文献综述、数据分析等)

                    请将文档保存为 'research_data/deep_research_alternatives_list.md'。

                    输出：deep_research_alternatives_list.md
                    ```        
                    请直接返回处理后的文档名称，不需要任何额外的解释或说明。
                    """},
                {"role": "user", "content": task_description}
            ]
        )
        
        doc_name = response.choices[0].message.content.strip()
        return doc_name
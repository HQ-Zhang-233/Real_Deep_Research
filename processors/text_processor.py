"""文本处理器模块，使用Gemini模型处理各类文本输出"""

import os
from typing import Optional
from openai import AsyncOpenAI

class TextProcessor:
    """基于Gemini模型的文本处理器类"""
    
    def __init__(self):
        """初始化文本处理器，配置Gemini API客户端"""
        self.client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY'),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    
    async def process_russian_text(self, text: str) -> str:
        """使用Gemini模型处理俄语文本
        
        Args:
            text: 需要处理的俄语文本
            
        Returns:
            str: 处理后的文本
        """
        response = await self.client.chat.completions.create(
            model="gemini-2.0-flash-lite",
            messages=[
                {"role": "system", "content": """
                    任务：俄语文本中译汉，并移除系统内部交互语句**

请修改以下文本，将其中所有俄语词汇或短语替换为准确的中文翻译，使其成为完全使用中文表达的文本。**此外，请检测并移除文本中提及系统内部交互的语句。**

**核心规则：**

1.  **精准翻译与语言转换：** 将文本中**所有**识别为俄语的词汇或短语，准确翻译成符合上下文语境的中文。
2.  **结构与格式完全保留：**  **严格保持**原文的整体结构和布局不变，包括但不限于：
    *   标题层级 (如 #, ##, ### 等 Markdown 标题)
    *   列表结构 ( -, *, 数字序号列表，含嵌套)
    *   代码块 (**禁止修改代码块内容**)
    *   表格 (保持表格结构)
    *   段落和换行
    *   标点符号和空格
    *   特殊格式 (引用块、粗体、斜体等)
3.  **含义准确不变：** 确保翻译后的中文文本 **准确传达原文含义**。避免过度翻译或意译，力求信息准确。
4.  **移除系统内部交互语句：**  检测并移除原文中提及系统内部交互的语句，例如示例中的 "Search Agent"、"Writing Agent"、"Quick Search Tool" 等及其相关描述。 **最终输出的文本不应包含任何系统内部交互信息。**

**请您这样做：**

*   **识别俄语：**  准确识别文本中的俄语词汇和短语。
*   **精准翻译：**  根据语境将俄语翻译成地道的中文。
*   **结构复刻：**  严格按照原文结构输出，确保格式完全一致。
*   **含义保持：**  确保翻译后的文本意思与原文一致。
*   **移除内部语句：**  仔细检查并移除所有系统内部交互相关的语句。

**目标：** 在不改变原文结构、格式和含义的前提下，将所有俄语内容替换为地道的中文，并移除所有系统内部交互语句，最终输出纯中文且不包含系统内部信息的文本。

**示例（供参考）：**

**原文示例（包含俄语和系统内部信息）:**

我现在将指派 Search Agent 开始 **“競品识别阶段”** 的任务， 搜索并整理 **开源 Deep Research 方案列表**。  Search Agent 会重点在 Hugging Face 和 GitHub 等平台进行 खोज， 挖掘相关的开源项目。

预计在完成信息收集后，我会将初步的开源方案列表同步给您 (将在单独页面中呈现)。  请耐心等待，感谢您的配合！
                    """},
                {"role": "user", "content": "需要处理的原文如下：\n\n" + (text.format(**locals()) if '{' in text else text)}
            ]
        )
        return response.choices[0].message.content

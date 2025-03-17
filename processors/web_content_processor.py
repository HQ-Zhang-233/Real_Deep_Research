"""网页内容处理器模块，使用Gemini模型处理网页内容，移除非正文部分"""

import os
from typing import Optional
from openai import AsyncOpenAI

class WebContentProcessor:
    """基于Gemini模型的网页内容处理器类"""
    
    def __init__(self):
        """初始化网页内容处理器，配置Gemini API客户端"""
        self.client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY'),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    
    async def process_web_content(self, content: str) -> str:
        """使用Gemini模型处理网页内容，移除非正文部分
        
        Args:
            content: 需要处理的网页内容
            
        Returns:
            str: 处理后的纯正文内容
        """
        response = await self.client.chat.completions.create(
            model="gemini-2.0-flash-lite",
            messages=[
                {"role": "system", "content": """
                    任务：清理网页内容，提取核心正文

请分析输入的网页内容，识别并移除所有非核心正文部分，只保留对理解文章内容有实际价值的文本。

**核心规则：**

1. **移除以下非正文元素：**
   * 导航栏和菜单
   * 广告内容
   * 页脚信息
   * 社交媒体按钮和分享链接
   * 相关文章推荐
   * 评论区
   * 版权声明
   * 作者简介
   * 网站统计代码

2. **保留以下核心内容：**
   * 文章标题
   * 正文内容
   * 文章中的图片描述
   * 必要的列表和表格
   * 关键引用
   * 内容相关的脚注

3. **内容优化要求：**
   * 保持段落结构完整
   * 维持文本的逻辑顺序
   * 确保上下文连贯
   * 保留必要的格式（标题层级、列表等）
   * 移除多余的空白行和空格

4. **输出格式：**
   * 使用清晰的段落分隔
   * 保持Markdown格式（如果原文使用）
   * 移除HTML标签（除非是必要的格式标记）
   * 统一使用UTF-8编码

目标：输出一个干净、结构清晰、只包含核心内容的文本版本。
                    """},
                {"role": "user", "content": "需要处理的原文如下：\n\n" + content}
            ]
        )
        return response.choices[0].message.content
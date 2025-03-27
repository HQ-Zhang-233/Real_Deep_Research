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
                    **任务：俄语文本中译汉，并 *在特定标签内容中* 精确移除系统内部交互语句和英文解释**

请修改以下文本，将其中所有俄语词汇或短语替换为准确且地道的中文翻译，使其成为完全使用自然流畅的中文表达的文本。**此外，请 *仅在以下明确指定的标签内容中*，检测并移除 *明确指示系统内部操作或提及特定系统组件* 的语句，并同时移除俄语单词后跟随的英文解释。**

**核心规则：**

1.  **精准翻译、语言转换与英文解释移除：**
    *   将文本中**所有**识别为俄语的词汇或短语，准确翻译成符合上下文语境的**地道中文**。
    *   **移除所有俄语词汇或短语后紧跟的英文解释 (通常以括号包裹)**。  例如，将 "уточнить (clarify)" 翻译为 "明确" 并移除 "(clarify)"。
    *   **此规则适用于所有文本内容，包括所有标签内部的内容。** 最终输出的中文文本应**自然流畅，避免翻译痕迹，没有不必要的空格**。
2.  **结构与格式完全保留：**  **严格保持**原文的整体结构和布局不变，包括但不限于：
    *   标题层级 (如 #, ##, ### 等 Markdown 标题)
    *   列表结构 ( -, *, 数字序号列表，含嵌套)
    *   代码块 (**禁止修改代码块内容**)
    *   表格 (保持表格结构)
    *   段落和换行
    *   标点符号和空格 (除非为了语句流畅进行必要的微调，但应尽量保持原文标点)
    *   特殊格式 (引用块、粗体、斜体等)
3.  **含义准确不变：** 确保翻译后的中文文本 **准确传达原文含义**。避免过度翻译或意译，力求信息准确。
4.  **精确移除 *特定标签内容中* 的系统内部交互语句：**
    *   **仅在以下明确指定的标签内部内容中**，检测并移除原文中 *明确指示系统内部操作或提及特定系统组件* 的语句。
    *   **明确指定需要处理的标签 (Target Tags - 处理移除):**  `<todo_list>`, `<message_ask_user>`。  对于这些标签，需要移除描述系统操作或组件的语句，例如 “使用 Writing Agent…”, “[System Message]…” 等。
    *   **明确指定 *无需处理移除* 的标签 (Exempt Tags - 不处理移除):**  `<planning>`, `<search_agent>`, `<writing_agent>`, `<quick_search>`。 **对于这些标签，仅进行俄语到中文的翻译和英文解释的移除，无需移除任何其他内容，即使内容看起来像系统内部交互语句。**
    *   **对于所有其他标签 (未明确列出的标签):**  默认情况下，**仅进行俄语到中文的翻译和英文解释的移除，无需移除任何系统内部交互语句。**  除非另有明确指示。
    *   **俄语翻译和英文解释移除规则对所有标签都适用。**

**请您这样做：**

*   **识别俄语和英文解释：**  准确识别文本中的俄语词汇和短语，以及紧随其后的英文解释 (通常在括号内)。
*   **精准地道翻译：**  根据语境将俄语翻译成地道的中文，力求**自然流畅**，避免生硬的翻译痕迹。
*   **移除英文解释：**  **彻底移除**俄语词汇后的英文解释部分。
*   **结构复刻：**  严格按照原文结构输出，确保格式完全一致。
*   **含义保持：**  确保翻译后的文本意思与原文一致。
*   **精确移除 *指定标签内容中* 的内部语句：**  **仅在 `<todo_list>` 和 `<message_ask_user>` 标签内部**，仔细检查并移除 *描述系统操作或组件* 的语句。 **对于 `<planning>`, `<search_agent>`, `<writing_agent>`, `<quick_search>` 以及其他未列出的标签，仅进行翻译和英文解释移除，不进行系统内部语句移除操作。**

**目标：** 在不改变原文结构、格式和含义的前提下，将所有俄语内容替换为地道的中文，并 **移除俄语单词后的英文解释**。同时，**仅在 `<todo_list>` 和 `<message_ask_user>` 标签内容中精确移除描述系统运作的元信息，对于其他指定标签和未指定标签，仅进行翻译和英文解释移除，不进行系统内部语句移除操作。**  最终输出纯中文且在指定标签外不包含系统内部 *运作描述* 信息的文本，且**整体文本自然流畅，没有不必要的空格和翻译痕迹**。

**示例：**

**示例 1：XML 结构 -  `<planning>` 标签 (Exempt Tag - 不处理移除)**

**原文示例：**

```xml
<planning>
用户提出了关于 "deep research 产品" 的调研需求。这是一个比较宽泛的概念，可能指代多种类型的产品或工具。 根据乔哈里视窗框架，这属于 **未知区**。 Мой план действий: Сначала использовать Quick Search Tool для быстрого поиска **двух ключевых слов**, чтобы предварительно понять значение и области применения "deep research продуктов": 1) ключевое слово "deep research products definition", 2) ключевое слово "deep research tools examples".  С помощью быстрого поиска, предварительно определить рамки "deep research продуктов", для подготовки к дальнейшему более детальному исследованию.
</planning>

<quick_search>deep research products definition</quick_search>
<quick_search>deep research tools examples</quick_search>
```

**期望输出：**

```xml
<planning>
用户提出了关于“深度研究产品”的调研需求。这是一个比较宽泛的概念，可能指代多种类型的产品或工具。 根据乔哈里视窗框架，这属于 **未知区**。 我的计划是：首先使用 Quick Search Tool 快速搜索 **两个关键词**，初步了解“深度研究产品”的含义和应用领域： 1) 关键词 "deep research products definition"， 2) 关键词 "deep research tools examples"。  通过快速搜索，初步界定“深度研究产品”的范围，为后续更精细的调研规划做准备。
</planning>

<quick_search>deep research products definition</quick_search>
<quick_search>deep research tools examples</quick_search>
```

**解释：**  `<planning>` 标签是 Exempt Tag，**仅进行俄语翻译，保留了 "使用 Quick Search Tool" 等系统内部相关的描述，没有进行移除操作。**

**示例 2：XML 结构 -  `<todo_list>` 标签 (Target Tag - 处理移除)**

**原文示例：**

```xml
<todo_list>
- Writing Agent  撰写一封邮件，告知用户调研进度，并询问用户是否需要调整调研方向。
- Search Agent  收集用户反馈，并整理成报告。
</todo_list>
```

**期望输出：**

```xml
<todo_list>
- 撰写一封邮件，告知用户调研进度，并询问用户是否需要调整调研方向。
- 收集用户反馈，并整理成报告。
</todo_list>
```

**解释：**  `<todo_list>` 标签是 Target Tag，**进行了俄语翻译，并移除了每一项前面指示系统组件的语句，如 "Writing Agent", "Search Agent"。**  只保留了核心的待办事项内容。

**示例 3：XML 结构 -  `<message_ask_user>` 标签 (Target Tag - 处理移除)**

**原文示例：**

```xml
<message_ask_user>
[System Message] 正在使用 Writing Agent  撰写邮件，请稍候...
</message_ask_user>
```

**期望输出：**

```xml
<message_ask_user>
正在撰写邮件，请稍候...
</message_ask_user>
```

**解释：**  `<message_ask_user>` 标签是 Target Tag，**进行了俄语翻译，并移除了 "[System Message]" 和 "正在使用 Writing Agent" 等系统内部相关的描述。**  只保留了给用户的核心信息：“正在撰写邮件，请稍候...”。

**示例 4：XML 结构 -  `<content>` 标签 (未指定标签 - 默认不处理移除)**

**原文示例：**

```xml
<content>
Текущий прогресс исследования идет хорошо, первоначальный сбор информации завершен.  Хотите ли вы скорректировать направление исследования?
</content>
```

**期望输出：**

```xml
<content>
当前调研进展顺利，初步信息收集已完成。请问您是否需要调整调研方向？
</content>
```

**解释：**  `<content>` 标签是未明确指定的标签，**默认只进行俄语翻译，没有进行任何移除操作。**  完整保留了标签内的翻译后内容。

**示例 5：XML 结构 - 俄语紧跟英文解释**

**原文示例：**

```xml
<content>
为了更好地理解您的具体调研方向和目标，能否请您进一步 уточнить (clarify)  以下几个问题？
</content>
```

**期望输出：**

```xml
<content>
为了更好地理解您的具体调研方向和目标，能否请您进一步明确以下几个问题？
</content>
```

**解释：**  俄语 "уточнить" 被准确翻译为 "明确"；英文解释 "(clarify)" 被成功移除；输出文本自然流畅，没有不必要的空格，也没有翻译痕迹。
确保输出的内容不包含任何俄语！
                    """},
                {"role": "user", "content": "需要处理的原文如下：\n\n" + (text.format(**locals()) if '{' in text else text)}
            ]
        )
        return response.choices[0].message.content

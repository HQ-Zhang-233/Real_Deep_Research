from typing import Dict
from bs4 import BeautifulSoup

def extract_xml_tags(text: str) -> Dict[str, list]:
    """
    提取XML标签内容，支持带属性和嵌套场景
    
    Args:
        text: 包含XML标签的文本，可能包含Markdown代码块
        
    Returns:
        字典格式的标签名到内容列表的映射，相同标签名的内容会被存储在同一个列表中
    """
    result = {}
    
    def wrap_with_cdata(text: str) -> str:
        """将文本包装在CDATA中以保护内部XML标签"""
        return f'<![CDATA[{text}]]>'
    try:
        # 处理Markdown代码块
        if text.startswith('```xml'):
            text = text[6:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        # 预处理XML标签内容，将内容包装在CDATA中
        import re
        # 首先处理反引号中的标签引用，将其转义
        backtick_pattern = r'`<[^`]+>`'
        def escape_backtick_tags(match):
            return match.group(0).replace('<', '&lt;').replace('>', '&gt;')
        text = re.sub(backtick_pattern, escape_backtick_tags, text)
        
        # 处理真实的XML标签内容
        pattern = r'(<[^>]+>)([^<]+)(</[^>]+>)'
        
        def replace_content(match):
            start_tag, content, end_tag = match.groups()
            return f'{start_tag}{wrap_with_cdata(content)}{end_tag}'
        
        text = re.sub(pattern, replace_content, text)
        soup = BeautifulSoup(f'<root>{text}</root>', 'lxml-xml')
        print('解析后的XML结构：', soup.prettify())  # 调试输出
        
        # 递归提取所有子标签
        def extract_nested_tags(element):
            if hasattr(element, 'children'):
                for child in element.children:
                    if child.name:
                        # 统一标签命名为下划线格式
                        tag_name = ''.join(['_' + c.lower() if c.isupper() else c for c in child.name]).lstrip('_')
                        # 提取标签内容，处理CDATA
                        content = ''.join(str(item) for item in child.contents)
                        # 移除CDATA标记
                        content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', content)
                        content = content.strip()
                        # 将内容添加到对应标签的列表中
                        if content:  # 只有当内容不为空时才添加
                            if tag_name in result:
                                result[tag_name].append(content)
                            else:
                                result[tag_name] = [content]
                        # 提取标签属性
                        if child.attrs:
                            attr_key = f'{tag_name}.attrs'
                            if attr_key in result:
                                result[attr_key].append(str(child.attrs))
                            else:
                                result[attr_key] = [str(child.attrs)]
                        # 递归处理子标签
                        extract_nested_tags(child)
        
        extract_nested_tags(soup.root)
                
    except Exception as e:
        print(f"XML解析错误: {str(e)}")
        
    return result


def main():
    test_case = '''
    ```xml
<planning>
我分析了 Quick Search 结果， 发现 “deep research” 可能有以下几种含义:

1. **具体的产品名称:** 搜索结果中出现了 OpenAI, Perplexity 和 Gemini 等公司推出的名为 “Deep Research” 的产品或功能。  这些产品似乎都是 AI 驱动的，旨在帮助用户进行更深入的研究。
2. **研究方法论:**  部分搜索结果提到了 “deep research methodology”，  可能指代一种深度研究的方法。

为了更准确地理解用户的需求，并开展有针对性的调研，  我需要向用户 clarifying questions, 明确他们想要调研的 “deep research” 具体是指哪种含义。  根据乔哈里视窗框架，这属于 **盲区 -> 开放区** 的过程。  我需要通过提问，将用户已知但模型未知的信息挖掘出来，转化为模型和用户共同已知的开放区信息。

我的规划是：

1.  **向用户提问 (Message to User):**  在 `<message_ask_user>` 中，  列出我在 Quick Search 结果中发现的 “deep research” 的几种可能含义，  请用户选择他们感兴趣的具体方向， 或者提供更详细的描述。  问题需要清晰、简洁，避免技术术语，方便用户理解和回答。
2.  **等待用户回复:**  在收到用户回复之前，  我不会进行下一步的任务规划或 Agent 调用。

本次 Agent 输出只包含 `<message_ask_user>` 标签， 用于向用户提问以明确需求。  暂不更新 Todo List， 待用户回复明确调研方向后再进行 Todo List 的构建和更新。
</planning>

<message_ask_user>
您好！ 感谢您提出 “deep research” 的调研需求。  为了更好地理解您的目标，能否请您 уточнить 您想要调研的 “deep research” 具体是指什么呢？

根据我初步的搜索结果，“deep research” 可能有以下几种含义：

1.  **AI 产品名称 (例如 OpenAI Deep Research, Perplexity Deep Research, Gemini Deep Research):**  指一些公司推出的，  以 “Deep Research” 命名的 AI 驱动的研究工具或产品。  如果您想调研的是这类 AI 产品，能否告知是哪一家或哪几家的产品？ 或者您更关注哪种类型或功能的 AI 研究产品？
2.  **研究方法论:**  指代一种深度研究的方法或理念。  如果您想调研的是 “deep research” 作为一种研究方法，  能否 уточнить 您 интересуетесь 哪种领域或类型的深度研究方法？

请您 уточнить 您 интересуетесь 以上哪种含义的 “deep research” ， 或者提供更详细的描述，  以便我更好地为您规划后续的调研任务。  谢谢！
</message_ask_user>
```
'''
    print('xx/n', extract_xml_tags(test_case))

if __name__ == '__main__':
    main()
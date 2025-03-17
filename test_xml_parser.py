import xml.etree.ElementTree as ET
from typing import Dict
from io import StringIO
from bs4 import BeautifulSoup

def extract_xml_tags(text: str) -> Dict[str, str]:
    """提取所有XML标签内容，包括带属性的标签
    
    Args:
        text: 包含XML标签的文本
        
    Returns:
        Dict[str, str]: 标签名称到内容的映射
        
    Example:
        >>> text = '<message>Hello</message><data key="value">Content</data>'
        >>> result = extract_xml_tags(text)
        >>> print(result)
        {'message': 'Hello', 'data': 'Content'}
    """
    result = {}
    try:
        # 移除可能存在的Markdown代码块标记
        if text.startswith('```xml'):
            text = text[6:]
        if text.endswith('```'):
            text = text[:-3]
            
        # 确保XML文本格式正确
        text = text.strip()
        if not text:
            return result
            
        # 使用BeautifulSoup解析XML
        soup = BeautifulSoup(f'<root>{text}</root>', 'xml')
        
        # 提取所有直接子标签的内容
        for child in soup.root.children:
            if child.name:  # 跳过NavigableString对象
                tag_name = child.name
                content = child.get_text(strip=True)
                result[tag_name] = content
                
    except Exception as e:
        print(f"处理XML时发生错误: {str(e)}")
        
    return result

def main():
    # 测试用例
    test_cases = [
        # 带空格和换行的标签
        '''```xml
<planning>
用户提出了 "deepresearch这类产品" 的竞品调研需求。  根据乔哈里视窗框架，这属于 **未知区**。  我需要先快速了解 "deepresearch" 这类产品可能指代什么，以及竞品调研的具体目标和范围。

我的初步规划思路是：

1.  **Quick Search (未知区 -> 隐藏区/开放区):** 使用 Quick Search Tool 快速搜索 "deep research products"，"competitive intelligence platforms"，"market research software" 等关键词，初步了解 "deepresearch 这类产品" 可能指代的产品类型和市场范围。  这将帮助我从完全的未知区进入到对相关产品类型有初步了解的隐藏区/开放区。
2.  **Message to User (隐藏区/开放区 -> 盲区/开放区):**  在快速搜索的基础上，向用户提问， уточнить  "deepresearch这类产品" 的具体指代，以及竞品调研的具体目标、关注的竞争维度、目标用户画像等关键信息。  通过提问，将用户脑海中已知但模型未知的 "盲区" 信息挖掘出来，转化为双方都清晰的 "开放区" 信息。
3.  **Todo List 初步规划 (开放区):**  根据用户回复，细化竞品调研的具体任务，例如 "识别主要竞争对手"，"分析竞品的功能特点"，"评估竞品的优劣势"，"总结市场竞争格局" 等，形成初步的 Todo List。

**信息获取策略：**  优先使用 Quick Search Tool 快速探索 "deepresearch 这类产品" 的定义和范围，然后通过 `<message_ask_user>` 主动向用户提问，明确用户需求，将未知区转化为开放区。  初期不直接指派 Search Agent 进行深度搜索，避免在用户需求不明确的情况下进行无效的信息收集。
</planning>

<quick_search query="deep research products"></quick_search>
<quick_search query="competitive intelligence platforms"></quick_search>
<quick_search query="market research software"></quick_search>

<message_ask_user>
您好！ 很高兴为您进行 "deepresearch这类产品" 的竞品调研。  为了更好地理解您的需求，并产出高质量的调研结果，能否请您提供更多关于 "deepresearch这类产品" 的信息？  例如：

1.  **您所说的 "deepresearch这类产品" 具体指的是什么类型的工具或平台？**  例如，是指像 Gartner、Forrester 这样的市场研究报告平台，还是指提供竞争情报分析、市场趋势洞察的软件，亦或是其他类型的研究工具？  如果您有具体的竞品名称，也欢迎告知。
2.  **本次竞品调研的目的是什么？**  是为了了解市场竞争格局，为产品定位提供参考，还是为了学习竞品的优势，改进自身产品，或是其他目的？
3.  **您希望重点关注哪些竞争维度？**  例如，是产品功能、技术特点、目标用户、市场定价、营销策略、用户评价，还是其他方面？
4.  **您是否有已经确定的主要竞争对手？**  如果有，请列出竞品名称，这将有助于我更精准地聚焦调研范围。

请您尽可能详细地描述您的需求，这将帮助我更准确地规划调研任务，并为您提供更有价值的竞品分析报告。  感谢您的配合！
</message_ask_user>
```'''
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"输入: {test_case}")
        result = extract_xml_tags(test_case)
        print(f"输出: {result}")

if __name__ == '__main__':
    main()
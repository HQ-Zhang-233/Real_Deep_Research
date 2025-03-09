import requests
import uuid
import json
from tools.zhipu_search import ZhipuSearchTool

# 替换为您的真实 API KEY
api_key = "a0ffea5e932043fd845093e87a3b44b4.NXzJ7EHlT7Af6nD5"

def run_web_search_pro(user_query):
    """
    调用 web-search-pro 搜索工具并返回结果。

    Args:
        user_query (str): 用户搜索query。

    Returns:
        dict: API 响应的 JSON 字典。如果请求失败，则返回 None。
    """
    url = "https://open.bigmodel.cn/api/paas/v4/tools"
    tool = "web-search-pro"
    request_id = str(uuid.uuid4())
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'  # 明确指定 Content-Type 为 JSON
    }
    data = {
        "request_id": request_id,
        "tool": tool,
        "stream": False, # 同步调用
        "messages": [
            {
                "role": "user",
                "content": user_query
            }
        ]
    }

    try:
        resp = requests.post(
            url,
            headers=headers,
            data=json.dumps(data), # 使用 json.dumps() 将 Python 字典转换为 JSON 字符串
            timeout=300
        )
        resp.raise_for_status()  # 检查请求是否成功，失败则抛出 HTTPError 异常
        return resp.json()  # 将响应内容解析为 JSON 格式
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None

def main():
    # 创建智谱搜索工具实例
    search_tool = ZhipuSearchTool()
    
    # 设置搜索query
    query = "中国队在最近的奥运会上获得了多少枚奖牌？"

    # 执行搜索
    search_result = search_tool.search(query)

    if search_result:
        # 打印原始JSON响应
        print("原始 JSON 响应:\n", json.dumps(search_result, indent=2, ensure_ascii=False))

        # 解析搜索结果
        # 确保 search_result 是字典类型
        if isinstance(search_result, list):
            search_result = search_result[0] if search_result else {}
        parsed_results = search_tool.parse_search_results(search_result)
        
        # 打印搜索意图
        print("\n搜索意图:")
        for intent_item in parsed_results['search_intents']:
            print(f"  - 意图类型: {intent_item['intent']}")
            print(f"  - 关键词: {intent_item['keywords']}")
            print(f"  - 分类: {intent_item['category']}")

        # 打印搜索结果
        print("\n搜索结果:")
        for result_item in parsed_results['search_results']:
            print(f"  - 标题: {result_item['title']}")
            print(f"  - 链接: {result_item['link']}")
            print(f"  - 来源媒体: {result_item['media']}")
            print(f"  - 内容摘要: {result_item['content'][:150]}...")

        # 打印使用统计
        usage = search_tool.get_usage_info(search_result)
        if usage:
            print("\nTokens 消耗:")
            print(f"  - Prompt Tokens: {usage['prompt_tokens']}")
            print(f"  - Completion Tokens: {usage['completion_tokens']}")
            print(f"  - Total Tokens: {usage['total_tokens']}")
    else:
        print("搜索请求失败，请检查错误信息。")

def test_raw_search_response():
    """
    测试智谱搜索的原始返回结果
    """
    # 初始化搜索工具
    search_tool = ZhipuSearchTool()
    
    # 设置测试查询
    query = "manus"
    
    # 执行搜索并获取原始结果
    raw_response = search_tool.search(query)
    
    # 打印完整的JSON响应（格式化输出）
    print("\n原始API响应:")
    print(json.dumps(raw_response, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    test_raw_search_response()
import requests
import uuid
import json
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

class ZhipuSearchTool:
    """智谱AI搜索工具"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化智谱搜索工具
        
        Args:
            api_key: 智谱API密钥，如果不提供则从环境变量获取
        """
        if not api_key:
            load_dotenv()
            api_key = os.getenv('ZHIPU_API_KEY')
            
        if not api_key:
            raise ValueError("需要提供 ZHIPU_API_KEY")
        
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/tools"

    def search(self, query: str, limit: int = 3) -> list:
        """
        使用智谱搜索引擎搜索中文内容
        
        Args:
            query: 搜索查询
            limit: 返回结果数量
            
        Returns:
            List[Dict]: 包含 title, content, link, index 的搜索结果列表
        """
        response = self._request_search(query)
        if not response:
            return []
        
        try:
            # 获取搜索结果
            choices = response.get('choices', [])
            if not choices:
                return []
            
            first_choice = choices[0]
            message = first_choice.get('message', {})
            tool_calls = message.get('tool_calls', [])
            
            results = []
            for tool_call in tool_calls:
                if tool_call.get('type') == 'search_result' and 'search_result' in tool_call:
                    search_results = tool_call['search_result']
                    for idx, item in enumerate(search_results):
                        results.append({
                            'title': item.get('title', ''),
                            'content': item.get('content', ''),
                            'link': item.get('link', ''),
                            'index': idx
                        })
            
            # 限制返回数量
            return results[:limit]
        
        except Exception as e:
            print(f"解析搜索结果出错: {str(e)}")
            return []

    def _request_search(self, query: str) -> Optional[Dict]:
        """执行搜索请求"""
        tool = "web-search-pro"
        request_id = str(uuid.uuid4())
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        data = {
            "request_id": request_id,
            "tool": tool,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        }

        try:
            resp = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(data),
                timeout=300
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            return None

    def parse_search_results(self, response: Dict) -> Dict[str, List]:
        """
        解析搜索结果
        
        Args:
            response: API响应的JSON字典
            
        Returns:
            包含搜索意图和结果的字典
        """
        parsed_results = {
            'search_intents': [],
            'search_results': []
        }
        
        if not response or 'choices' not in response:
            return parsed_results
            
        first_choice = response['choices'][0]
        if 'message' in first_choice and 'tool_calls' in first_choice['message']:
            tool_calls = first_choice['message']['tool_calls']
            
            for tool_call in tool_calls:
                if tool_call['type'] == 'search_intent' and 'search_intent' in tool_call:
                    parsed_results['search_intents'].extend(tool_call['search_intent'])
                elif tool_call['type'] == 'search_result' and 'search_result' in tool_call:
                    parsed_results['search_results'].extend(tool_call['search_result'])
                    
        return parsed_results

    def get_usage_info(self, response: Dict) -> Optional[Dict]:
        """
        获取API使用统计信息
        
        Args:
            response: API响应的JSON字典
            
        Returns:
            包含token使用信息的字典
        """
        if response and 'usage' in response:
            return response['usage']
        return None 
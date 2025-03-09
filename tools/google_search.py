from typing import List, Dict
import os
import requests
from dotenv import load_dotenv

class GoogleSearch:
    """Google搜索工具"""
    
    def __init__(self, api_key: str | None = None, custom_search_id: str | None = None):
        """初始化Google搜索工具"""
        if not api_key or not custom_search_id:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            custom_search_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
            
        if not api_key or not custom_search_id:
            raise ValueError("需要提供 GOOGLE_API_KEY 和 GOOGLE_SEARCH_ENGINE_ID")
        
        self.api_key: str = api_key  # type: ignore
        self.custom_search_id: str = custom_search_id  # type: ignore
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 10) -> dict:
        """
        执行搜索并返回结果
        
        Args:
            query: 搜索查询字符串
            num_results: 需要返回的结果数量
            
        Returns:
            dict: 包含搜索结果的字典
        """
        if not query.strip():
            return {"status": "error", "message": "搜索查询不能为空"}
        
        try:
            search_results = self._execute_search(query, num_results)
            if not search_results:
                return {
                    "status": "error",
                    "message": "未找到搜索结果",
                    "query": query
                }
            
            results = []
            for i, item in enumerate(search_results, 1):
                result = {
                    "index": i,
                    "title": item.get('title', ''),
                    "link": item.get('link', ''),
                    "snippet": item.get('snippet', '')
                }
                results.append(result)
            
            return {
                "status": "success",
                "query": query,
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }

    def _execute_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """执行Google搜索"""
        params = {
            'key': self.api_key,
            'cx': self.custom_search_id,
            'q': query,
            'num': min(num_results, 10)
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            results = response.json()
            
            if 'items' not in results:
                print("没有找到搜索结果")
                return []
                
            return results['items']
            
        except Exception as e:
            print(f"搜索出错: {str(e)}")
            return [] 
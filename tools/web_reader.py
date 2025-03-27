from typing import List, Dict, Optional
import asyncio
import requests
import re
import requests
from processors.web_content_processor import WebContentProcessor
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class WebReader:
    """网页内容阅读工具"""
    
    def __init__(self):
        """初始化网页阅读工具"""
        self.jina_base_url = "https://r.jina.ai/"
        self.content_processor = WebContentProcessor()

    async def read_pages(self, urls: List[str]) -> List[Dict]:
        """批量读取多个网页的内容"""
        tasks = [self._get_page_content(url) for url in urls]
        contents = await asyncio.gather(*tasks)
        
        results = []
        for url, content in zip(urls, contents):
            results.append({
                "url": url,
                "content": content if content else "无法获取内容"
            })
        
        return results

    async def read_page(self, url: str) -> Dict:
        """读取单个网页的内容"""
        content = await self._get_page_content(url)
        return {
            "url": url,
            "content": content if content else "无法获取内容"
        }

    async def _get_page_content(self, url: str) -> str:
        """获取网页内容或YouTube视频字幕"""
        # 检查是否为YouTube链接
        video_id = self._extract_video_id(url)
        if video_id:
            return self._get_best_transcript(video_id) or ''

        # 非YouTube链接，使用原有的网页内容获取逻辑
        try:
            response = requests.get(f"{self.jina_base_url}{url}")
            response.raise_for_status()
            raw_content = response.text
            # 使用WebContentProcessor优化网页内容
            processed_content = await self.content_processor.process_web_content(raw_content)
            return processed_content
        except Exception as e:
            print(f"获取页面内容失败: {str(e)}")
            return ''

    def _extract_video_id(self, url: str) -> Optional[str]:
        """从YouTube URL中提取视频ID"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]*)',
            r'(?:youtube\.com\/embed\/)([^&\n?]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _get_best_transcript(self, video_id: str) -> Optional[str]:
        """使用Coze API获取视频字幕"""
        try:
            # 从环境变量获取Coze API配置
            api_token = os.getenv('COZE_API_TOKEN')
            workflow_id = os.getenv('COZE_WORKFLOW_ID')
            
            if not api_token or not workflow_id:
                print("缺少Coze API配置")
                return None
            
            # 准备请求数据
            url = 'https://api.coze.com/v1/workflow/run'
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            data = {
                'parameters': {
                    'video_id': video_id
                },
                'workflow_id': workflow_id
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if result.get('code') == 0 and result.get('data'):
                # 解析data字段中的JSON字符串
                import json
                caption_data = json.loads(result['data'])
                return caption_data.get('caption', '')
            
            return None

        except Exception as e:
            print(f"无法获取视频 {video_id} 的字幕: {str(e)}")
            return None
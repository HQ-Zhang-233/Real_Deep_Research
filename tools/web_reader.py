from typing import List, Dict, Optional
import asyncio
import requests
import re
from youtube_transcript_api import YouTubeTranscriptApi

class WebReader:
    """网页内容阅读工具"""
    
    def __init__(self):
        """初始化网页阅读工具"""
        self.jina_base_url = "https://r.jina.ai/"

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
            return response.text
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
        """获取视频的最佳字幕，无重试机制"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 优先尝试获取英文或中文字幕
            for lang in ['en', 'zh']:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    return ' '.join([entry['text'] for entry in transcript.fetch()])
                except:
                    continue
            
            # 如果没有英文和中文，获取任意一个可用的字幕
            try:
                transcript = transcript_list.find_manually_created_transcript(['en', 'zh'])
                return ' '.join([entry['text'] for entry in transcript.fetch()])
            except:
                generated_transcripts = list(transcript_list._generated_transcripts.values())
                if generated_transcripts:
                    transcript = generated_transcripts[0]
                    return ' '.join([entry['text'] for entry in transcript.fetch()])
                return None

        except Exception as e:
            print(f"无法获取视频 {video_id} 的字幕: {str(e)}")
            return None
"""搜索代理模块

负责处理搜索相关的任务，包括信息检索和整合
"""

import os
import logging
import json
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from processors.xml_parser import extract_xml_tags
from processors.doc_name_processor import DocNameProcessor
from config.prompts.search_agent_prompt import get_search_agent_prompt
from tools.google_search import GoogleSearch
from tools.web_reader import WebReader

class SearchAgent:
    """搜索代理，负责执行搜索任务并整合信息"""
    
    def __init__(self, task_id: Optional[str] = None):
        """初始化搜索代理
        
        Args:
            task_id: 可选的任务ID，用于保存report等文件
        """
        # 初始化OpenAI客户端，配置为使用Gemini API
        self.client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY'),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.google_search = GoogleSearch()
        self.web_reader = WebReader()
        self.doc_name_processor = DocNameProcessor()
        self.task_id = task_id
        self.chat_history = []
        self.logger = None
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        if not self.task_id:
            return
            
        task_dir = self._ensure_task_directory()
        log_dir = os.path.join(task_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志文件
        log_file = os.path.join(log_dir, 'search_interaction.log')
        
        # 配置日志记录器
        self.logger = logging.getLogger(f'search_agent_{self.task_id}')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
    def _ensure_task_directory(self) -> str:
        """确保任务目录存在并返回路径"""
        if not self.task_id:
            return ""
            
        tasks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks')
        task_dir = os.path.join(tasks_dir, self.task_id)
        os.makedirs(os.path.join(task_dir, 'documents'), exist_ok=True)
        os.makedirs(os.path.join(task_dir, 'chat_history'), exist_ok=True)
        return task_dir
    
    async def extract_doc_name_from_task(self, task_description: str) -> str:
        """从任务描述中提取合适的文档名称
        
        Args:
            task_description: 任务描述文本
            
        Returns:
            str: 提取的文档名称
        """
        return await self.doc_name_processor.extract_doc_name(task_description)
    
    async def process_search_task(self, task_description: str) -> Dict[str, str]:
        """处理搜索任务
        
        Args:
            task_description: 搜索任务描述
            
        Returns:
            Dict[str, str]: 搜索结果，包含处理后的信息
        """
        # 获取模型响应
        system_prompt = get_search_agent_prompt()
        messages_to_send = [{"role": "system", "content": system_prompt}, {"role": "user", "content": task_description}] + self.chat_history

        if self.logger:
            # Log the messages being sent, including history
            self.logger.debug(f"发送给模型的消息列表:\nSystem Prompt: {system_prompt}\nTask Description: {task_description}\nChat History: {self.chat_history}")

        # Prepend initial messages to history *only once*
        if not self.chat_history:
             self.chat_history.append({"role": "system", "content": system_prompt})
             self.chat_history.append({"role": "user", "content": task_description})

        response = await self.client.chat.completions.create(
            model="gemini-2.0-flash",
            n=1,
            messages=messages_to_send # Send the combined list
        )
        
        model_response = response.choices[0].message.content
        if self.logger:
            self.logger.info(f"模型原始响应:\n{model_response}")
            
        self.chat_history.append({"role": "assistant", "content": model_response})
        
        # 提取标签内容
        tags = extract_xml_tags(model_response)
        if self.logger:
            self.logger.debug(f"提取的标签内容: {tags}")
        
        # 处理quick_search标签
        if 'quick_search' in tags:
            if self.logger:
                self.logger.info("执行快速搜索工具调用")
                
            search_results = []
            for query_str in tags['quick_search']:
                # 将搜索关键词按逗号分隔并去除空格
                queries = [q.strip() for q in query_str.split(',') if q.strip()]
                
                for query in queries:
                    if self.logger:
                        self.logger.debug(f"搜索查询: {query}")
                    result = self.google_search.search(query)
                    search_results.append({"query": query, "result": result})
                    
                    # 将搜索结果添加到历史记录
                    self.chat_history.append({
                        "role": "user",
                        "content": f"Quick Search Results for '{query}':\n{str(result)}"
                    })
            
            # 如果有搜索结果，递归处理新的响应
            if search_results:
                if self.logger:
                    self.logger.debug(f"搜索结果: {search_results}")
                return await self.process_search_task(task_description)
        
        # 处理webpage_read标签
        if 'webpage_read' in tags:
            if self.logger:
                self.logger.info("执行网页读取工具调用")
                
            for url in tags['webpage_read']:
                if self.logger:
                    self.logger.debug(f"读取网页: {url}")
                # 读取网页内容
                page_content = await self.web_reader.read_page(url)
                # 将内容添加到历史记录
                self.chat_history.append({
                    "role": "user",
                    "content": f"Webpage Content for '{url}':\n{str(page_content)}"
                })
            # 递归处理新的响应
            return await self.process_search_task(task_description)
        
        # 处理report标签
        if 'report' in tags and self.task_id:
            if self.logger:
                self.logger.info("处理report标签")
                
            # 获取report内容
            report_content = tags['report'][0] if tags['report'] else ""
            
            # 保存report到任务目录
            task_dir = self._ensure_task_directory()
            if task_dir:
                # 从任务描述中提取文档名称
                doc_name = await self.extract_doc_name_from_task(task_description)
                report_path = os.path.join(task_dir, 'documents', f'{doc_name}')
                if self.logger:
                    self.logger.debug(f"保存report到: {report_path}")
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                    
                # Save chat history after saving the report
                chat_history_dir = os.path.join(task_dir, 'chat_history')
                chat_history_file = os.path.join(chat_history_dir, 'search_agent_chat_history.json')
                if self.logger:
                    self.logger.debug(f"保存对话历史到: {chat_history_file}")
                try:
                    with open(chat_history_file, 'w', encoding='utf-8') as f_hist:
                        json.dump(self.chat_history, f_hist, ensure_ascii=False, indent=4)
                except Exception as e:
                     if self.logger:
                        self.logger.error(f"保存对话历史失败: {e}")
                        
                # 只有在成功保存report时才返回最终结果
                result = {
                    "status": "success",
                    "task_completed": True,
                    "documents": {
                        "report_path": report_path
                    },
                    "source": "search_agent"
                }
                return result
        
        # 如果没有report标签或保存失败，继续递归处理
        return await self.process_search_task(task_description)
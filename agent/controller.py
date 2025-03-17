import os
import asyncio
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openai import AsyncOpenAI
from config.prompts.planner_agent_prompt import get_default_prompt
from tools.google_search import GoogleSearch

class ControllerAgent:
    """主控Agent，负责处理用户输入并与模型交互"""
    
    def __init__(self, task_id: Optional[str] = None):
        """初始化控制器
        Args:
            task_id: 可选的任务ID，如果提供则加载已有任务的历史记录
        """
        self.client = None
        self.google_search = None
        self.tasks_dir = None
        self.current_task_id = None
        self.chat_history = []
        self.logger = None
        self._init_task = self.async_init(task_id)

    def _setup_logger(self):
        """设置日志记录器"""
        if not self.current_task_id:
            return
            
        task_dir = self._ensure_task_directory()
        log_dir = os.path.join(task_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志文件
        log_file = os.path.join(log_dir, 'interaction.log')
        
        # 配置日志记录器
        self.logger = logging.getLogger(f'controller_{self.current_task_id}')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    async def async_init(self, task_id: Optional[str] = None):
        """异步初始化
        Args:
            task_id: 可选的任务ID，如果提供则加载已有任务的历史记录
        """
        # 初始化OpenAI客户端，配置为使用Gemini API
        self.client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY'),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        # 初始化Google搜索工具
        self.google_search = GoogleSearch()
        # 创建任务根目录
        self.tasks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks')
        os.makedirs(self.tasks_dir, exist_ok=True)
        # 当前任务ID和聊天历史
        self.current_task_id = task_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_history = []
        
        # 设置日志记录器
        self._setup_logger()
        
        # 如果提供了任务ID，尝试加载已有的聊天历史
        if task_id:
            await self._load_chat_history()
    
    def extract_xml_tags(self, text: str) -> Dict[str, str]:
        """提取所有XML标签内容，包括带属性的标签"""
        # 每次调用时重新初始化结果字典
        result = {}
        # 使用正则表达式匹配所有XML标签，包括带属性的标签
        pattern = re.compile(r'<([^\s>]+)[^>]*>(?:([^<]*)|.*?</\1>)', re.DOTALL)
        matches = pattern.findall(text)
        
        # 将所有标签内容存储到字典中
        for tag_name, content in matches:
            content = content.strip()
            
        return result

    def _ensure_task_directory(self) -> str:
        """确保任务目录存在并返回当前任务目录路径"""
        if not self.current_task_id:
            # 生成新的任务ID
            self.current_task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # 获取任务目录路径
        task_dir = os.path.join(self.tasks_dir, self.current_task_id)
        os.makedirs(task_dir, exist_ok=True)
        
        # 创建子目录
        os.makedirs(os.path.join(task_dir, 'chat_history'), exist_ok=True)
        os.makedirs(os.path.join(task_dir, 'documents'), exist_ok=True)
        
        return task_dir

    def _save_chat_history(self):
        """保存聊天历史到文件"""
        if not self.current_task_id:
            return
            
        task_dir = self._ensure_task_directory()
        history_file = os.path.join(task_dir, 'chat_history', 'conversation.json')
        
        with open(history_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(self.chat_history, f, ensure_ascii=False, indent=2)

    async def _load_chat_history(self):
        """从文件加载聊天历史"""
        if not self.current_task_id:
            return
            
        task_dir = self._ensure_task_directory()
        history_file = os.path.join(task_dir, 'chat_history', 'conversation.json')
        
        if not os.path.exists(history_file):
            return
            
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                import json
                self.chat_history = json.load(f)
        except Exception as e:
            print(f"加载聊天历史时发生错误: {str(e)}")
            self.chat_history = []
    
    async def _process_model_response(self, input_content: str) -> str:
        """处理模型响应并执行必要的工具调用"""
        # 构建消息列表
        messages = [
            {"role": "system", "content": get_default_prompt()}
        ] + self.chat_history
        
        if self.logger:
            self.logger.debug(f"发送给模型的消息列表: {messages}")
        
        # 获取模型响应
        response = await self.client.chat.completions.create(
            model="gemini-2.0-flash-thinking-exp-01-21",
            n=1,
            messages=messages
        )
        
        model_response = response.choices[0].message.content
        if self.logger:
            self.logger.info(f"模型原始响应:\n{model_response}")
        
        self.chat_history.append({"role": "assistant", "content": model_response})
        
        # 提取标签内容
        tags = self.extract_xml_tags(model_response)
        if self.logger:
            self.logger.debug(f"提取的标签内容: {tags}")
        
        # 如果需要执行工具调用
        if 'quick_search' in tags:
            if self.logger:
                self.logger.info("执行快速搜索工具调用")
            # 执行搜索并收集结果
            search_results = []
            query_matches = re.finditer(r'<quick_search[^>]*query="([^"]+)"[^>]*>', model_response)
            
            for match in query_matches:
                query = match.group(1)
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
                return await self._process_model_response(input_content)
        
        # 处理todo_list标签
        if 'todo_list' in tags:
            if self.logger:
                self.logger.info("处理todo_list标签")
            todo_content = tags['todo_list']
            # 临时的俄语解析器函数
            processed_content = self._temp_russian_processor(todo_content)
            
            # 确保任务目录存在
            task_dir = self._ensure_task_directory()
            
            # 使用固定的todo list文件名
            filepath = os.path.join(task_dir, 'documents', 'todo_list.md')
            
            # 保存处理后的todo list
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            if self.logger:
                self.logger.debug(f"保存todo list到: {filepath}")
        
        # 返回用户消息或空字符串
        return tags.get("message_ask_user", "")

    async def process_input(self, user_input: str) -> str:
        """处理用户输入并返回响应
        Args:
            user_input: 用户输入的文本
        Returns:
            str: 处理后的响应文本
        """
        if self.logger:
            self.logger.info(f"收到用户输入: {user_input}")
        
        # 将用户输入添加到聊天历史
        self.chat_history.append({"role": "user", "content": user_input})
        
        # 处理用户输入并获取响应
        response = await self._process_model_response(user_input)
        
        # 保存聊天历史
        self._save_chat_history()
        
        if self.logger:
            self.logger.info(f"返回给用户的响应: {response}")
        
        return response
    
    def _temp_russian_processor(self, content: str) -> str:
        """临时的俄语处理器，后续会替换为真实的实现"""
        # 这里仅返回原始内容，后续会实现真正的俄语处理逻辑
        return content
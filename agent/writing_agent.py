"""写作代理模块

负责处理文档写作相关的任务，包括读取文档、整合内容和生成报告
"""

import os
import logging
import json
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from processors.xml_parser import extract_xml_tags
from processors.doc_name_processor import DocNameProcessor
from config.prompts.writing_agent_prompt import get_writing_agent_prompt

class WritingAgent:
    """写作代理，负责执行写作任务并生成报告"""
    
    def __init__(self, task_id: Optional[str] = None):
        self.file_handler = None  # 用于存储文件处理器引用
        """初始化写作代理
        
        Args:
            task_id: 可选的任务ID，用于读取和保存文档
        """
        # 初始化OpenAI客户端，配置为使用Gemini API
        self.client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY'),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
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
        log_file = os.path.join(log_dir, 'writing_interaction.log')
        
        # 配置日志记录器
        self.logger = logging.getLogger(f'writing_agent_{self.task_id}')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.file_handler = file_handler  # 保存处理器引用

    def __del__(self):
        """析构函数用于资源清理"""
        try:
            if self.file_handler:
                # 关闭并移除文件处理器
                self.file_handler.close()
                self.logger.removeHandler(self.file_handler)
                # 移除日志记录器引用
                del self.logger
                del self.file_handler
        except Exception as e:
            pass  # 防止析构时出现异常
        finally:
            # 确保最终解除引用
            self.logger = None
            self.file_handler = None
        
    def _ensure_task_directory(self) -> str:
        """确保任务目录存在并返回路径"""
        if not self.task_id:
            return ""
            
        tasks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks')
        task_dir = os.path.join(tasks_dir, self.task_id)
        os.makedirs(os.path.join(task_dir, 'documents'), exist_ok=True)
        os.makedirs(os.path.join(task_dir, 'chat_history'), exist_ok=True)
        return task_dir
    
    def _read_document(self, doc_path: str) -> str:
        """读取文档内容
        
        Args:
            doc_path: 文档路径
            
        Returns:
            str: 文档内容
        """
        try:
            task_dir = self._ensure_task_directory()
            if not task_dir:
                if self.logger:
                    self.logger.error("Task directory is not available")
                return ""
                
            # 如果传入的是完整路径，直接使用
            if os.path.isabs(doc_path):
                final_path = doc_path
            # 如果路径中已包含documents目录，只需要拼接task_dir
            elif 'documents' in doc_path:
                final_path = os.path.join(task_dir, doc_path)
            else:
                # 否则按照当前逻辑拼接task_dir和documents目录
                final_path = os.path.join(task_dir, 'documents', doc_path)
                
            if not os.path.exists(final_path):
                if self.logger:
                    self.logger.error(f"File not found: {final_path}")
                return ""
                
            with open(final_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if self.logger:
                    self.logger.debug(f"Successfully read file: {final_path}")
                return content
        except Exception as e:
            print(f"Error reading document {doc_path}: {str(e)}")
            return ""
    
    def _get_documents_in_task(self) -> List[str]:
        """获取任务目录下的所有文档路径"""
        task_dir = self._ensure_task_directory()
        if not task_dir:
            return []
            
        docs_dir = os.path.join(task_dir, 'documents')
        if not os.path.exists(docs_dir):
            return []
            
        return [os.path.join(docs_dir, f) for f in os.listdir(docs_dir) 
                if os.path.isfile(os.path.join(docs_dir, f))]
    
    async def extract_doc_name_from_task(self, task_description: str) -> str:
        """从任务描述中提取合适的文档名称
        
        Args:
            task_description: 任务描述文本
            
        Returns:
            str: 提取的文档名称
        """
        return await self.doc_name_processor.extract_doc_name(task_description)
    
    async def process_writing_task(self, task_description: str) -> Dict[str, str]:
        """处理写作任务
        
        Args:
            task_description: 写作任务描述
            
        Returns:
            Dict[str, str]: 写作结果，包含处理后的信息
        """
        # 获取任务目录下的所有文档
        documents = self._get_documents_in_task()
        doc_contents = {}
        todo_list = ""
        document_list = ""
        
        # 获取任务目录
        task_dir = self._ensure_task_directory()
        
        # 读取所有文档内容并生成树形文档列表
        for doc_path in documents:
            doc_name = os.path.basename(doc_path)
            doc_contents[doc_name] = self._read_document(doc_path)
            # 获取相对于documents目录的路径
            rel_path = os.path.relpath(doc_path, os.path.join(task_dir, 'documents'))
            # 计算缩进级别
            indent_level = len(os.path.dirname(rel_path).split(os.sep))
            # 添加缩进的文档条目
            document_list += f"{'  ' * indent_level}- {doc_name}\n"
            
            # 如果是todo_list.md文件，读取其内容
            if doc_name == "todo_list.md":
                todo_list = doc_contents[doc_name]
            
        # 生成文档预览信息
        doc_previews = ""
        if doc_contents:
            doc_previews = "\n".join([f"- {name}: {content[:200]}..." 
                                   for name, content in doc_contents.items()])
        
        # 获取模型响应
        system_prompt = get_writing_agent_prompt(todo_list, document_list, doc_previews)
        messages_to_send = [{"role": "system", "content": system_prompt}, {"role": "user", "content": task_description}] + self.chat_history

        if self.logger:
            # Log the messages being sent, including history
            self.logger.debug(f"发送给模型的消息列表:\nSystem Prompt: [Prompt content omitted for brevity]\nTask Description: {task_description}\nChat History: {self.chat_history}")

        # Prepend initial messages to history *only once*
        if not self.chat_history:
             self.chat_history.append({"role": "system", "content": system_prompt})
             self.chat_history.append({"role": "user", "content": task_description})
            
        response = await self.client.chat.completions.create(
            model="gemini-2.0-flash-thinking-exp-01-21",
            n=1,
            messages=messages_to_send
        )
        
        model_response = response.choices[0].message.content
        if self.logger:
            self.logger.info(f"模型原始响应:\n{model_response}")
            
        self.chat_history.append({"role": "assistant", "content": model_response})
        
        # 提取标签内容
        tags = extract_xml_tags(model_response)
        if self.logger:
            self.logger.debug(f"提取的标签内容: {tags}")
        
        # 处理file_read标签
        if 'file_read' in tags:
            if self.logger:
                self.logger.info("执行文件读取工具调用")
                
            file_contents = []
            for file_paths_str in tags['file_read']:
                # 将文件路径按逗号分隔并去除空格
                file_paths = [p.strip() for p in file_paths_str.split(',') if p.strip()]
                
                for file_path in file_paths:
                    if self.logger:
                        self.logger.debug(f"读取文件: {file_path}")
                    # 读取文件内容
                    file_content = self._read_document(os.path.join(task_dir, 'documents', file_path))
                    file_contents.append({"path": file_path, "content": file_content})
                    
                    # 将文件内容添加到历史记录
                    self.chat_history.append({
                        "role": "user",
                        "content": f"File Content ({file_path}):\n{file_content}"
                    })
            
            # 如果有读取到文件内容，递归处理新的响应
            if file_contents:
                if self.logger:
                    self.logger.debug(f"文件读取结果: {file_contents}")
                return await self.process_writing_task(task_description)
        
        # 获取任务目录
        task_dir = self._ensure_task_directory()
        
        # 处理report标签
        if 'report' in tags and self.task_id:
            if self.logger:
                self.logger.info("处理report标签")
                
            # 获取report内容
            report_content = tags['report'][0] if tags['report'] else ""
            
            # 保存report到任务目录
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
                chat_history_file = os.path.join(chat_history_dir, 'writing_agent_chat_history.json')
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
                        "report_path": report_path if 'report' in tags and task_dir else None
                    },
                    "source": "writing_agent"
                }
                return result
        
        # 返回最终结果
        result = {
            "status": "success",
            "task_completed": True,
            "documents": {
                "report_path": report_path if 'report' in tags and task_dir else None
            },
            "source": "writing_agent"
        }
        return result
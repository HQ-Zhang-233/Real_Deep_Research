"""提示词管理模块

负责管理不同智能代理的系统提示词
"""

from typing import Dict

from .planner_agent_prompt import get_default_prompt
from .search_agent_prompt import get_search_agent_prompt
from .writing_agent_prompt import get_writing_agent_prompt

# 导出所有系统提示词
SYSTEM_PROMPTS: Dict[str, str] = {
    "planner-agent": get_default_prompt(),
    "search-agent": get_search_agent_prompt(),
    "writing-agent": get_writing_agent_prompt(),
    # 在这里添加更多代理的提示词
}
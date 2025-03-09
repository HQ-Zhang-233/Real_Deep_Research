"""提示词管理模块

负责管理不同智能代理的系统提示词
"""

from typing import Dict

from .planner_agent_prompt import get_default_prompt
from .researcher import get_researcher_prompt
from .searcher_agent_prompt import get_deepseek_chat_prompt

# 导出所有系统提示词
SYSTEM_PROMPTS: Dict[str, str] = {
    "planner-agent": get_default_prompt(),
    "researcher": get_researcher_prompt(),
    "searcher-agent": get_deepseek_chat_prompt(),
    # 在这里添加更多代理的提示词
}
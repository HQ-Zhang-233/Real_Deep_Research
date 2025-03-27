import os
import asyncio
from agent.controller import ControllerAgent
import config  # 确保环境变量在程序启动时被加载

def list_tasks(tasks_dir):
    """列出所有可用的任务"""
    tasks = []
    try:
        # 获取所有任务目录
        for task_id in os.listdir(tasks_dir):
            task_path = os.path.join(tasks_dir, task_id)
            if os.path.isdir(task_path):
                tasks.append(task_id)
        return sorted(tasks, reverse=True)  # 最新的任务排在前面
    except Exception as e:
        print(f"读取任务列表时发生错误: {str(e)}")
        return []

async def main():
    # 获取任务目录
    tasks_dir = os.path.join(os.path.dirname(__file__), 'tasks')
    os.makedirs(tasks_dir, exist_ok=True)
    
    print("欢迎使用对话系统！")
    print("1. 创建新任务")
    print("2. 继续已有任务")
    
    choice = input("请选择 (1/2): ").strip()
    
    task_id = None
    if choice == "2":
        # 列出所有可用的任务
        tasks = list_tasks(tasks_dir)
        if not tasks:
            print("没有找到可用的任务，将创建新任务。")
        else:
            print("\n可用的任务:")
            for i, task_id in enumerate(tasks, 1):
                print(f"{i}. {task_id}")
            
            while True:
                try:
                    task_index = int(input("\n请选择任务编号 (或按Enter创建新任务): ").strip() or "0") - 1
                    if task_index == -1:
                        break
                    if 0 <= task_index < len(tasks):
                        task_id = tasks[task_index]
                        break
                    print("无效的选择，请重试。")
                except ValueError:
                    print("请输入有效的数字。")
    
    # 创建控制器实例
    controller = ControllerAgent(task_id)
    await controller._init_task
    
    print("\n输入 'quit' 或 'exit' 退出。")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n用户: ").strip()
            
            # 检查是否退出
            if user_input.lower() in ['quit', 'exit']:
                print("再见！")
                break
            
            # 如果输入为空，继续下一轮
            if not user_input:
                continue
            
            # 处理用户输入并获取响应
            response = await controller.process_input(user_input)
            print(f"\n助手: {response}")
            
        except KeyboardInterrupt:
            print("\n程序被中断，正在退出...")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

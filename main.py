import asyncio
from agent.controller import ControllerAgent

async def main():
    # 创建控制器实例
    controller = ControllerAgent()
    await controller._init_task
    
    print("欢迎使用对话系统！输入 'quit' 或 'exit' 退出。")
    
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

from tools.youtube_search import YouTubeSearchTool

def main():
    try:
        # 创建YouTube搜索工具实例
        youtube_tool = YouTubeSearchTool()
        
        # 搜索视频并获取字幕
        results = youtube_tool.search_youtube_videos("DeepResearch", 2)
        
        # 打印结果
        for i, result in enumerate(results, 1):
            print(f"\n--- 结果 {i} ---")
            print(f"标题: {result['title']}")
            print(f"链接: {result['link']}")
            print(f"视频ID: {result['video_id']}")
            if result['transcript']:
                print(f"字幕预览: {result['transcript'][:200]}...")
            else:
                print("无字幕")
                
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()

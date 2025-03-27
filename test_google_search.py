from tools.google_search import GoogleSearch

def main():
    # 创建Google搜索工具实例
    google_search = GoogleSearch()
    
    # 设置搜索查询
    query = "open source AI research tools"
    
    print(f"\n执行搜索查询: {query}")
    result = google_search.search(query)
    
    # 打印搜索结果
    if result['status'] == 'success':
        print(f"\n找到 {len(result['results'])} 条结果:")
        for item in result['results']:
            print(f"\n{item['index']}. {item['title']}")
            print(f"链接: {item['link']}")
            print(f"摘要: {item['snippet']}")
    else:
        print(f"搜索失败: {result['message']}")

if __name__ == '__main__':
    main()
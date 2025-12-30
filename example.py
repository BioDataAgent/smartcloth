"""
智能穿衣助理使用示例
"""
from my_agent01.agent import clothing_assistant, query_with_logging


def main():
    """示例：使用智能穿衣助理"""
    
    # 示例 1：使用带日志的查询函数（推荐）
    print("=" * 50)
    print("示例 1：查询北京后天的天气和穿衣建议")
    print("=" * 50)
    response = query_with_logging(clothing_assistant, "北京后天")
    print("\n智能体回复：")
    print(response)
    print("\n" + "=" * 50 + "\n")
    
    # 示例 2：直接使用智能体
    print("=" * 50)
    print("示例 2：查询上海明天的天气和穿衣建议")
    print("=" * 50)
    response = clothing_assistant.query("上海明天")
    print("\n智能体回复：")
    print(response)
    print("\n" + "=" * 50 + "\n")
    
    # 示例 3：查询具体日期
    print("=" * 50)
    print("示例 3：查询广州 2025-12-30 的天气和穿衣建议")
    print("=" * 50)
    response = query_with_logging(clothing_assistant, "广州 2025-12-30")
    print("\n智能体回复：")
    print(response)


if __name__ == "__main__":
    main()


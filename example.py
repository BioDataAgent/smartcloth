"""
智能穿衣助理使用示例

注意：
1. 此文件需要在项目根目录下运行
2. 使用前需要设置 Google API Key 环境变量
3. 可以通过以下方式设置：
   export GOOGLE_API_KEY="your-api-key-here"
   或者在代码中设置：os.environ["GOOGLE_API_KEY"] = "your-api-key-here"
"""
import os
import sys
from pathlib import Path

# 检查环境变量
if not os.getenv("GOOGLE_API_KEY"):
    print("⚠️  警告：未检测到 GOOGLE_API_KEY 环境变量")
    print("请先设置 Google API Key：")
    print("  export GOOGLE_API_KEY='your-api-key-here'")
    print("或者取消下面代码的注释并填入你的 API Key：")
    print("  os.environ['GOOGLE_API_KEY'] = 'your-api-key-here'")
    print()
    # 如果需要，可以在这里直接设置（不推荐提交到 Git）
    # os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

# 添加当前目录到 Python 路径，以便导入模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from agent import clothing_assistant, query_with_logging


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


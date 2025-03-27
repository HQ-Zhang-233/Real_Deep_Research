from dotenv import load_dotenv
import os

# 获取项目根目录的路径
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

# 加载.env文件
load_dotenv(os.path.join(ROOT_DIR, '.env'))
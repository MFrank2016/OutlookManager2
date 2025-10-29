"""
开发服务器启动脚本
"""
import sys
from pathlib import Path

# 将 backend 目录添加到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动 Outlook Manager v3.0 开发服务器...")
    print(f"📁 项目目录: {backend_dir}")
    print(f"🐍 Python 路径: {sys.path[0]}")
    print()
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

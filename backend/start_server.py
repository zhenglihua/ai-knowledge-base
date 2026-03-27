import uvicorn
import os

# 从环境变量获取端口，默认为8000
port = int(os.environ.get('PORT', 8000))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

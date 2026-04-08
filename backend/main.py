from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.kimi_router import router as kimi_router
from routers.sandbox_router import router as sandbox_router
from routers.project_router import router as project_router
from routers.audio_router import router as audio_router
from services.project_service import init_db

@asynccontextmanager
async def lifespan(app):
    """应用生命周期：启动时初始化数据库"""
    init_db()
    print("✅ SQLite 数据库初始化完成")
    yield

app = FastAPI(title="AI Engineer Platform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # 动态匹配所有跨域来源，解决 wildcard 与 credentials 的冲突
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kimi_router)
app.include_router(sandbox_router)
app.include_router(project_router)
app.include_router(audio_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Engineer Platform Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


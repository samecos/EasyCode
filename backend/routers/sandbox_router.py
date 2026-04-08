from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from services.sandbox_service import run_sandbox_code, run_sandbox_code_stream

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])

class ExecuteRequest(BaseModel):
    code: str
    params: Dict[str, Any]
    dependencies: list[str] = []
    demo_mode: bool = False
    project_id: Optional[str] = None

@router.post("/execute")
def execute_generated_code(req: ExecuteRequest):
    result = run_sandbox_code(req.code, req.params, req.dependencies, req.project_id)
    return result

@router.post("/execute_stream")
def execute_stream(req: ExecuteRequest):
    return StreamingResponse(
        run_sandbox_code_stream(req.code, req.params, req.dependencies, req.demo_mode, req.project_id),
    )

class OpenDirRequest(BaseModel):
    path: str

@router.post("/open_dir")
def open_system_directory(req: OpenDirRequest):
    import os, sys, subprocess
    path = req.path
    if not path or not os.path.exists(path):
        return {"success": False, "message": "系统找不到这层目录，可能文件还未生成或路径不存在"}
        
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return {"success": True, "message": "已经通过操作系统的文件浏览器打开指定目录！"}
    except Exception as e:
        return {"success": False, "message": f"底层打开指令执行失败: {str(e)}"}

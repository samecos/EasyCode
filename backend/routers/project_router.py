"""
工程管理 API 路由 (Phase 9)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from services.project_service import (
    create_project, list_projects, get_project,
    save_project, delete_project, copy_node_to_project
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


class SaveProjectRequest(BaseModel):
    name: str
    description: str = ""
    chat_logs: List[Dict[str, Any]] = []
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


class CopyNodeRequest(BaseModel):
    source_node_id: str
    target_project_id: str


@router.post("")
def api_create_project(req: CreateProjectRequest):
    """创建新工程"""
    project = create_project(req.name, req.description)
    return {"success": True, "project": project}


@router.get("")
def api_list_projects():
    """获取所有工程列表"""
    projects = list_projects()
    return {"success": True, "projects": projects}


@router.get("/{project_id}")
def api_get_project(project_id: str):
    """获取工程完整详情"""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="工程不存在")
    return {"success": True, "project": project}


@router.put("/{project_id}")
def api_save_project(project_id: str, req: SaveProjectRequest):
    """全量保存工程快照"""
    ok = save_project(project_id, req.model_dump())
    if not ok:
        raise HTTPException(status_code=404, detail="工程不存在，无法保存")
    return {"success": True, "message": "工程已保存"}


@router.delete("/{project_id}")
def api_delete_project(project_id: str):
    """删除工程"""
    ok = delete_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="工程不存在")
    return {"success": True, "message": "工程已删除"}


@router.post("/{project_id}/copy-node")
def api_copy_node(project_id: str, req: CopyNodeRequest):
    """复制节点到目标工程"""
    result = copy_node_to_project(req.source_node_id, req.target_project_id)
    if not result:
        raise HTTPException(status_code=404, detail="源节点或目标工程不存在")
    return {"success": True, "new_node": result}

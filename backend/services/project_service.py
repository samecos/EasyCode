"""
工程持久化存储服务 (Phase 9)
基于 SQLite 实现工程、节点、连线的完整 CRUD
"""
import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "projects.db")


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接，启用外键约束"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据库表结构（幂等，可重复调用）"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                chat_logs   TEXT DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS nodes (
                id           TEXT PRIMARY KEY,
                project_id   TEXT NOT NULL,
                label        TEXT DEFAULT '',
                prompt       TEXT DEFAULT '',
                code         TEXT DEFAULT '',
                parameters   TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                steps        TEXT DEFAULT '[]',
                position_x   REAL DEFAULT 300,
                position_y   REAL DEFAULT 100,
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS edges (
                id         TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                source     TEXT NOT NULL,
                target     TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ==================== 工程 CRUD ====================

def create_project(name: str, description: str = "") -> Dict[str, Any]:
    """创建新工程"""
    now = datetime.now().isoformat()
    project_id = str(uuid.uuid4())
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at, chat_logs) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, name, description, now, now, "[]")
        )
        conn.commit()
        return {"id": project_id, "name": name, "description": description, "created_at": now, "updated_at": now}
    finally:
        conn.close()


def list_projects() -> List[Dict[str, Any]]:
    """获取所有工程列表（按更新时间倒序），不含节点详情"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, description, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        result = []
        for row in rows:
            project = dict(row)
            # 附加节点数量统计
            count = conn.execute("SELECT COUNT(*) FROM nodes WHERE project_id = ?", (row["id"],)).fetchone()[0]
            project["node_count"] = count
            result.append(project)
        return result
    finally:
        conn.close()


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """获取工程完整详情：含所有节点、连线、对话记录"""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            return None

        project = dict(row)
        project["chat_logs"] = json.loads(project["chat_logs"])

        # 加载所有节点
        node_rows = conn.execute("SELECT * FROM nodes WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()
        nodes = []
        for n in node_rows:
            nd = dict(n)
            nd["parameters"] = json.loads(nd["parameters"])
            nd["dependencies"] = json.loads(nd["dependencies"])
            nd["steps"] = json.loads(nd["steps"])
            nodes.append(nd)
        project["nodes"] = nodes

        # 加载所有连线
        edge_rows = conn.execute("SELECT * FROM edges WHERE project_id = ?", (project_id,)).fetchall()
        project["edges"] = [dict(e) for e in edge_rows]

        return project
    finally:
        conn.close()


def save_project(project_id: str, data: Dict[str, Any]) -> bool:
    """
    全量保存工程快照：
    data 包含 { name?, description?, chat_logs?, nodes: [...], edges: [...] }
    """
    now = datetime.now().isoformat()
    conn = _get_conn()
    try:
        # 检查工程是否存在
        existing = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not existing:
            return False

        # 更新工程元信息
        conn.execute(
            "UPDATE projects SET name=?, description=?, chat_logs=?, updated_at=? WHERE id=?",
            (
                data.get("name", ""),
                data.get("description", ""),
                json.dumps(data.get("chat_logs", []), ensure_ascii=False),
                now,
                project_id
            )
        )

        # 清空旧节点和连线，重新写入（全量快照策略，简单可靠）
        conn.execute("DELETE FROM nodes WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM edges WHERE project_id = ?", (project_id,))

        # 写入节点
        for node in data.get("nodes", []):
            conn.execute(
                """INSERT INTO nodes (id, project_id, label, prompt, code, parameters, dependencies, steps, position_x, position_y, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    node["id"],
                    project_id,
                    node.get("label", node.get("prompt", "")),
                    node.get("prompt", ""),
                    node.get("code", ""),
                    json.dumps(node.get("parameters", []), ensure_ascii=False),
                    json.dumps(node.get("dependencies", []), ensure_ascii=False),
                    json.dumps(node.get("steps", []), ensure_ascii=False),
                    node.get("position_x", 300),
                    node.get("position_y", 100),
                    node.get("created_at", now),
                    now
                )
            )

        # 写入连线
        for edge in data.get("edges", []):
            conn.execute(
                "INSERT INTO edges (id, project_id, source, target) VALUES (?, ?, ?, ?)",
                (edge["id"], project_id, edge["source"], edge["target"])
            )

        conn.commit()
        return True
    finally:
        conn.close()


def delete_project(project_id: str) -> bool:
    """硬删除工程（含所有节点和连线，由 ON DELETE CASCADE 保证）"""
    conn = _get_conn()
    try:
        cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def copy_node_to_project(source_node_id: str, target_project_id: str) -> Optional[Dict[str, Any]]:
    """复制节点到目标工程"""
    conn = _get_conn()
    try:
        # 读取源节点
        row = conn.execute("SELECT * FROM nodes WHERE id = ?", (source_node_id,)).fetchone()
        if not row:
            return None

        # 检查目标工程是否存在
        target = conn.execute("SELECT id FROM projects WHERE id = ?", (target_project_id,)).fetchone()
        if not target:
            return None

        now = datetime.now().isoformat()
        new_id = f"node_{uuid.uuid4().hex[:8]}"
        source = dict(row)

        # 计算目标工程中的节点数量，用于定位
        count = conn.execute("SELECT COUNT(*) FROM nodes WHERE project_id = ?", (target_project_id,)).fetchone()[0]

        conn.execute(
            """INSERT INTO nodes (id, project_id, label, prompt, code, parameters, dependencies, steps, position_x, position_y, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_id,
                target_project_id,
                source["label"] + " (副本)",
                source["prompt"],
                source["code"],
                source["parameters"],
                source["dependencies"],
                source["steps"],
                300,
                100 + count * 230,
                now,
                now
            )
        )
        conn.commit()

        # 更新目标工程的 updated_at
        conn.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, target_project_id))
        conn.commit()

        return {"id": new_id, "target_project_id": target_project_id}
    finally:
        conn.close()

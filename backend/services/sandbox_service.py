import sys
import traceback
import tempfile
import subprocess
import os
import json
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def run_sandbox_code(code_str: str, params: dict, dependencies: List[str] = None, project_id: str = None) -> Dict[str, Any]:
    """
    真正的全抛弃型隔离沙箱 (Phase 5)
    具有独立的 pip 依赖安装控制和彻底的操作系统级子进程阻断
    """
    if dependencies is None:
        dependencies = []

    result = {
        "status": "success",
        "logs": "",
        "error": None
    }
    
    try:
        # 1. 创立隔离生命周期的临时宿主文件夹
        with tempfile.TemporaryDirectory() as temp_dir:
            libs_dir = None
            if project_id:
                venv_dir = os.path.join(DATA_DIR, "projects", project_id, "venv")
                if not os.path.exists(venv_dir):
                    result["logs"] += "⏳ 正在为工程建立隔离沙箱虚拟环境 (venv)...\n"
                    subprocess.run([sys.executable, "-m", "venv", venv_dir])
                
                if sys.platform == "win32":
                    python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
                else:
                    python_exe = os.path.join(venv_dir, "bin", "python")
                    
                install_cmd = [python_exe, "-m", "pip", "install", "--disable-pip-version-check", "-q"] + dependencies
            else:
                libs_dir = os.path.join(temp_dir, "libs")
                install_cmd = [sys.executable, "-m", "pip", "install", "--target", libs_dir, "--disable-pip-version-check", "-q"] + dependencies
                python_exe = sys.executable
            
            if dependencies and len(dependencies) > 0:
                result["logs"] += f"⏬ 开始为短暂沙箱预装第三方库: {', '.join(dependencies)}...\n"
                process_install = subprocess.run(install_cmd, capture_output=True, text=True, encoding="utf-8")
                
                if process_install.returncode != 0:
                     result["status"] = "error"
                     result["error"] = f"【底层依赖加载失败，极大可能是大模型幻觉提供了错误的库名，请在图谱参数白名单核实或删除】\n{process_install.stderr}"
                     result["logs"] += "❌ [终端拦截]：隔离依赖库安装流程阻断，沙箱提前销毁终止。\n"
                     return result
                result["logs"] += "✅ 依赖库组装就绪。\n"

            params_file = os.path.join(temp_dir, "params.json")
            script_file = os.path.join(temp_dir, "script.py")
            
            with open(params_file, "w", encoding="utf-8") as f:
                json.dump(params, f, ensure_ascii=False)
                
            wrapper_code = f"""
import json
import sys
import os

try:
    with open(r'{params_file}', 'r', encoding='utf-8') as f:
        __injected_params__ = json.load(f)
    globals().update(__injected_params__)
except Exception as e:
    print("【系统层级通知】沙箱运行环境变量注入失败:", e)

# ======= 以下为工程师编写及大模型核心生成的代码 =======
{code_str}
"""
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(wrapper_code)

            env = os.environ.copy()
            if libs_dir and os.path.exists(libs_dir):
                env["PYTHONPATH"] = libs_dir
                
            result["logs"] += "▶ 沙箱已启动，运行代码中...\n"
            process_run = subprocess.run(
                [python_exe, script_file], 
                env=env,
                capture_output=True, 
                text=True, 
                encoding="utf-8",
                cwd=temp_dir
            )
            
            result["logs"] += "---------------------------\n"
            result["logs"] += process_run.stdout
            
            if process_run.returncode != 0:
                result["status"] = "error"
                result["error"] = process_run.stderr
                
    except Exception as e:
        result["status"] = "error"
        result["error"] = "守护沙箱运行调度系统自身发生崩溃:\n" + traceback.format_exc()

    return result

def run_sandbox_code_stream(code_str: str, params: dict, dependencies: List[str] = None, demo_mode: bool = False, project_id: str = None):
    """
    (Phase 7) 沙箱流式执行环境，支持 SSE (Server-Sent Events) 实况转播与慢动作探针
    融入工程级缓存机制，如果指定了 project_id 则第三方库存储到持久化目录。
    """
    if dependencies is None:
        dependencies = []

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            libs_dir = None
            if project_id:
                venv_dir = os.path.join(DATA_DIR, "projects", project_id, "venv")
                if not os.path.exists(venv_dir):
                    yield f"data: {json.dumps({'type': 'log', 'content': '⏳ 初次运行当前工程，正在为工程建立隔离沙箱虚拟环境 (venv)...\\n'})}\n\n"
                    subprocess.run([sys.executable, "-m", "venv", venv_dir])
                
                if sys.platform == "win32":
                    python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
                else:
                    python_exe = os.path.join(venv_dir, "bin", "python")
                    
                install_cmd = [python_exe, "-m", "pip", "install", "--disable-pip-version-check", "-q"] + dependencies
            else:
                libs_dir = os.path.join(temp_dir, "libs")
                install_cmd = [sys.executable, "-m", "pip", "install", "--target", libs_dir, "--disable-pip-version-check", "-q"] + dependencies
                python_exe = sys.executable
            
            if dependencies and len(dependencies) > 0:
                yield f"data: {json.dumps({'type': 'log', 'content': f'⏬ 开始为短暂沙箱预装第三方库 {dependencies}...\\n'})}\n\n"
                
                process_install = None
                try:
                    process_install = subprocess.Popen(
                        install_cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT, 
                        text=True, 
                        encoding="utf-8",
                        errors="replace"
                    )
                    for line in iter(process_install.stdout.readline, ''):
                        yield f"data: {json.dumps({'type': 'log', 'content': line})}\n\n"
                    
                    process_install.wait()
                    if process_install.returncode != 0:
                        yield f"data: {json.dumps({'type': 'error', 'content': '❌底层依赖加载异常拦截，强制中断运行。\\n'})}\n\n"
                        return
                    yield f"data: {json.dumps({'type': 'log', 'content': '✅ 依赖库组装就绪。\\n'})}\n\n"
                finally:
                    if process_install and process_install.poll() is None:
                        process_install.kill()
                        process_install.wait()

            params_file = os.path.join(temp_dir, "params.json")
            script_file = os.path.join(temp_dir, "script.py")
            
            with open(params_file, "w", encoding="utf-8") as f:
                json.dump(params, f, ensure_ascii=False)

            import re
            if demo_mode:
                code_str = re.sub(
                    r'#\s*\[__BLOCK_MARK__:\s*(\d+)\].*',
                    r"print('\\n[SYSTEM_SYNC_STEP_POINTER]: \g<1>', flush=True)\nimport time; time.sleep(1.5)",
                    code_str
                )
            else:
                code_str = re.sub(r'#\s*\[__BLOCK_MARK__:\s*(\d+)\].*', "", code_str)

            wrapper_code = f"""import json
import sys
import os

try:
    with open(r'{params_file}', 'r', encoding='utf-8') as f:
        __injected_params__ = json.load(f)
    globals().update(__injected_params__)
except Exception as e:
    print("【沙箱引擎通讯】外部参数注入失败:", e)

# ======= 以下为工程师编写及大模型核心生成的代码 =======
{code_str}
"""
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(wrapper_code)

            env = os.environ.copy()
            # 强制不使用输出缓存，否则 python 的 print 要等到结束才出来
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            if libs_dir and os.path.exists(libs_dir):
                env["PYTHONPATH"] = libs_dir
                
            yield f"data: {json.dumps({'type': 'log', 'content': '▶ 沙箱守护进程已拉起，动态环境交接完毕，执行中...\\n\\n'})}\n\n"
            
            process_run = None
            try:
                process_run = subprocess.Popen(
                    [python_exe, script_file], 
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # 合并标准错误到标准输出
                    text=True, 
                    encoding="utf-8",
                    errors="replace",
                    cwd=temp_dir
                )
                
                # 流式逐行推送
                for line in iter(process_run.stdout.readline, ''):
                    yield f"data: {json.dumps({'type': 'log', 'content': line})}\n\n"
                
                process_run.wait()
                
                if process_run.returncode != 0:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'\\n\\n[Sandbox Exception] 子进程异常退出，状态码 {process_run.returncode}\\n'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'log', 'content': '\\n✅ 沙箱生命周期完结，执行干净退出。\\n'})}\n\n"
            finally:
                if process_run and process_run.poll() is None:
                    try:
                        process_run.kill()
                        process_run.wait()
                    except Exception:
                        pass

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': '系统守护级调度崩溃:\\n' + traceback.format_exc()})}\n\n"

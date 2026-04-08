from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
from services.kimi_service import stream_kimi_for_plan, stream_kimi_for_code, stream_kimi_for_plan_refine, stream_kimi_for_fix, stream_kimi_for_code_chat

router = APIRouter(prefix="/api/kimi", tags=["kimi"])

class PromptRequest(BaseModel):
    prompt: str

class GenerateRequest(BaseModel):
    prompt: str
    plan: Dict[str, Any]
    
class RefineRequest(BaseModel):
    prompt: str
    old_plan: Dict[str, Any]

class FixRequest(BaseModel):
    original_code: str
    terminal_output: str
    user_feedback: str = ""

class CodeChatRequest(BaseModel):
    current_code: str
    instruction: str

@router.post("/plan_stream")
def plan_stream(req: PromptRequest):
    return StreamingResponse(stream_kimi_for_plan(req.prompt), media_type="text/event-stream")

@router.post("/plan_refine_stream")
def refine_plan_stream(req: RefineRequest):
    return StreamingResponse(stream_kimi_for_plan_refine(req.old_plan, req.prompt), media_type="text/event-stream")

@router.post("/generate_stream")
def generate_code_stream(req: GenerateRequest):
    return StreamingResponse(stream_kimi_for_code(req.prompt, req.plan), media_type="text/event-stream")

@router.post("/fix_stream")
def fix_code_stream(req: FixRequest):
    return StreamingResponse(stream_kimi_for_fix(req.original_code, req.terminal_output, req.user_feedback), media_type="text/event-stream")

@router.post("/code_chat_stream")
def code_chat_stream(req: CodeChatRequest):
    return StreamingResponse(stream_kimi_for_code_chat(req.current_code, req.instruction), media_type="text/event-stream")

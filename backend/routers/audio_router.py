import os
import tempfile
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.audio_service import transcribe_audio_file

router = APIRouter(prefix="/api/audio", tags=["audio"])

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="未收到音频文件")
        
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".webm"
        # 写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            chunk = await file.read()
            tmp.write(chunk)
            tmp_path = tmp.name
        
        print(f"📥 收到音频文件: {file.filename}, 大小: {len(chunk)} 字节, 后缀: {suffix}")
            
        wav_path = tmp_path
        # 判断是否为 webm，用内嵌 ffmpeg 强制转换为 16kHz mono WAV
        if not tmp_path.endswith('.wav'):
            import imageio_ffmpeg
            import subprocess
            wav_path = tmp_path + ".wav"
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            print(f"🔄 正在用 ffmpeg 将 {suffix} 转换为 16kHz WAV...")
            subprocess.run(
                [ffmpeg_exe, "-y", "-i", tmp_path, "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", wav_path],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print(f"✅ 格式转换完毕: {wav_path}")
        
        # 调用核心推理
        print("🧠 开始 SenseVoice ONNX 推理...")
        result_text = transcribe_audio_file(wav_path)
        print(f"✅ 识别结果: {result_text}")
        
        # 用后即焚
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if wav_path != tmp_path and os.path.exists(wav_path):
            os.remove(wav_path)
            
        return {"text": result_text}
        
    except Exception as e:
        print(f"❌ 语音识别处理异常:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


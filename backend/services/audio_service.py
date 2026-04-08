import os
import tarfile
import urllib.request
import wave
import struct
import sherpa_onnx

# ==================== 模型自动下载管理 ====================

# 模型存储在后端的 models 目录下（不污染项目主目录）
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_BASE_DIR, "..", "models")

_MODEL_NAME = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
_MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{_MODEL_NAME}.tar.bz2"
_MODEL_DIR = os.path.join(_MODELS_DIR, _MODEL_NAME)

_recognizer_instance = None

def _ensure_model_downloaded():
    """首次运行时自动从 GitHub 下载并解压 SenseVoice ONNX 模型"""
    if os.path.exists(_MODEL_DIR):
        return  # 已缓存，跳过
    
    os.makedirs(_MODELS_DIR, exist_ok=True)
    tar_path = os.path.join(_MODELS_DIR, "model.tar.bz2")
    
    print(f"🔽 首次运行：正在从 GitHub 下载 SenseVoice ONNX 模型 (~200MB)...")
    print(f"   下载地址: {_MODEL_URL}")
    print(f"   存储目录: {_MODEL_DIR}")
    urllib.request.urlretrieve(_MODEL_URL, tar_path)
    print("📦 下载完毕，正在解压模型文件...")
    
    with tarfile.open(tar_path, "r:bz2") as tar:
        tar.extractall(path=_MODELS_DIR)
    
    # 清理压缩包
    if os.path.exists(tar_path):
        os.remove(tar_path)
    
    print("✅ SenseVoice ONNX 模型部署完毕！后续启动将自动秒载。")

def get_recognizer():
    """获取或创建全局的 ONNX 离线识别器（单例模式）"""
    global _recognizer_instance
    if _recognizer_instance is None:
        _ensure_model_downloaded()
        
        _recognizer_instance = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=os.path.join(_MODEL_DIR, "model.int8.onnx"),
            tokens=os.path.join(_MODEL_DIR, "tokens.txt"),
            language="auto",
            use_itn=True,
            num_threads=4,
            provider="cpu",
        )
    return _recognizer_instance

def transcribe_audio_file(file_path: str) -> str:
    """
    接受 16kHz mono WAV 文件路径，返回纯文本。
    由 router 层保证 webm -> wav 的格式转换。
    """
    recognizer = get_recognizer()
    
    with wave.open(file_path, "rb") as f:
        assert f.getnchannels() == 1, "音频必须是单声道"
        assert f.getframerate() == 16000, "音频采样率必须是 16kHz"
        num_frames = f.getnframes()
        raw_data = f.readframes(num_frames)
    
    # 将 int16 PCM 数据转换为 float32 样本列表
    samples = []
    for i in range(0, len(raw_data), 2):
        sample = struct.unpack_from('<h', raw_data, i)[0]
        samples.append(sample / 32768.0)
    
    stream = recognizer.create_stream()
    stream.accept_waveform(16000, samples)
    recognizer.decode_stream(stream)
    
    result = stream.result.text.strip()
    
    # SenseVoice 输出可能带有语种/情绪标签，清理掉
    # 例如: "<|zh|><|NEUTRAL|><|Speech|><|woitn|>你好世界"
    import re
    result = re.sub(r'<\|[^|]*\|>', '', result).strip()
    
    return result

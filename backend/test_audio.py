import sherpa_onnx
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_NAME = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
MODEL_DIR = os.path.join(MODELS_DIR, MODEL_NAME)

with open("probe_result.txt", "w", encoding="utf-8") as f:
    f.write("=== sherpa_onnx top-level ===\n")
    for name in sorted(dir(sherpa_onnx)):
        if not name.startswith("_"):
            f.write(f"  {name}\n")
    
    f.write("\n=== OfflineRecognizer dir ===\n")
    for name in sorted(dir(sherpa_onnx.OfflineRecognizer)):
        if not name.startswith("_"):
            f.write(f"  {name}\n")
    
    f.write(f"\nModel dir exists: {os.path.exists(MODEL_DIR)}\n")
    if os.path.exists(MODEL_DIR):
        f.write(f"Model dir contents: {os.listdir(MODEL_DIR)}\n")

print("Done! Check probe_result.txt")

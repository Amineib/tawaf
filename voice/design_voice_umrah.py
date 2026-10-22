"""Design the narrator voice for the Umrah tour's Arabic duas (Qwen3-TTS VoiceDesign).

Qwen3-TTS has no Arabic, so this only designs the *timbre*: it writes 4 candidate
reference clips (English text). duas_arabic.py then clones the chosen one with
Chatterbox Multilingual, which does speak Arabic.

Run:
  source .venv-mlx/bin/activate
  python design_voice_umrah.py
Writes umrah_voice/ref_1.wav ... ref_4.wav
"""
import os
import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"

VOICE = (
    "A gentle, warm man in his fifties with a deep, calm and reassuring voice, "
    "speaking slowly and reverently with very clear articulation, like an experienced "
    "guide softly helping elderly pilgrims in a quiet mosque. Steady, unhurried pace, "
    "natural pauses between phrases, humble and sincere, never theatrical, no echo."
)

TEXT = (
    "Take your time. There is no hurry here. "
    "Walk slowly, with the Kaaba on your left, and remember Allah in your heart. "
    "When you are tired, rest. Your journey is accepted, God willing."
)

os.makedirs("umrah_voice", exist_ok=True)
model = load_model(MODEL)
sr = getattr(model, "sample_rate", 24000)
for i, seed in enumerate([7, 21, 33, 58], start=1):
    mx.random.seed(seed)
    res = list(model.generate_voice_design(text=TEXT, language="English", instruct=VOICE))
    audio = np.concatenate([np.array(r.audio) for r in res])
    sf.write(f"umrah_voice/ref_{i}.wav", audio, sr)
    print("saved", f"umrah_voice/ref_{i}.wav", f"{len(audio) / sr:.1f}s")

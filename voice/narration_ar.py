"""Arabic narration for the Umrah tour, in the voice chosen for the duas
(umrah_voice/ref_4.wav), with Chatterbox Multilingual.

Run:
  source .venv/bin/activate
  PYTORCH_ENABLE_MPS_FALLBACK=1 python narration_ar.py                    # uses ref_4
  PYTORCH_ENABLE_MPS_FALLBACK=1 python narration_ar.py 4 tashkeel         # fully vowelled text
  PYTORCH_ENABLE_MPS_FALLBACK=1 python narration_ar.py 4 tashkeel sample  # 3 lines to compare first
Writes umrah_voice/narration_ar/<id>.wav for every line in umrah_voice/narration_ar.json
(tashkeel: reads narration_ar_tashkeel.json, made by tashkeel_ar.py, writes narration_ar_tashkeel/)
Already-generated lines are skipped, so you can stop and resume.
"""
import os, re, sys, json
import numpy as np
import soundfile as sf
import torch
from duas_arabic import load, trim

REF = f"umrah_voice/ref_{sys.argv[1] if len(sys.argv) > 1 else 4}.wav"
TASHKEEL = "tashkeel" in sys.argv[2:]
SAMPLE = "sample" in sys.argv[2:]
SRC = "umrah_voice/narration_ar_tashkeel.json" if TASHKEEL else "umrah_voice/narration_ar.json"
OUT = "umrah_voice/narration_ar_tashkeel" if TASHKEEL else "umrah_voice/narration_ar"
EXAGGERATION = 0.35
CFG_WEIGHT = 0.3
SEEDS = [21, 22, 23]
PAUSE = 0.4


def say(model, sentence):
    letters = sum(ch.isalpha() for ch in sentence)
    best = None
    for seed in SEEDS:
        torch.manual_seed(seed)
        wav = model.generate(sentence, language_id="ar", audio_prompt_path=REF,
                             exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
        a = trim(wav.squeeze().detach().cpu().numpy().astype(np.float32), model.sr)
        rate = letters / max(len(a) / model.sr, 0.1)
        score = abs(rate - 10.0)                 # calm Arabic narration ~10 letters/s
        if best is None or score < best[0]:
            best = (score, a, rate)
        if 7.0 <= rate <= 13.0:
            break
    return best[1], best[2]


def main():
    lines = json.load(open(SRC, encoding="utf-8"))
    if SAMPLE:
        lines = {k: lines[k] for k in ("ihram_2", "start_2", "marwa_1")}
    os.makedirs(OUT, exist_ok=True)
    model = load()
    sr = model.sr
    gap = np.zeros(int(PAUSE * sr), dtype=np.float32)
    for key, text in lines.items():
        path = f"{OUT}/{key}.wav"
        if os.path.exists(path):
            continue
        # split on sentence ends and on commas, so each take stays short and steady
        parts_txt = [s.strip() for s in re.split(r"(?<=[.؟!،])\s+", text) if s.strip()]
        parts = []
        for s in parts_txt:
            a, rate = say(model, s)
            parts += [a, gap]
        out = np.concatenate(parts[:-1])
        out *= 0.89 / (float(np.abs(out).max()) or 1.0)
        sf.write(path, out, sr)
        print(f"{key:12s} {len(out) / sr:5.1f}s")
    print(f"\nDone: {OUT}/")


if __name__ == "__main__":
    main()

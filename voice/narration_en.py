"""English narration for the Umrah tour, cloned from the chosen designed voice
(umrah_voice/ref_1.wav) with Chatterbox Multilingual.

Run:
  source .venv/bin/activate
  PYTORCH_ENABLE_MPS_FALLBACK=1 python narration_en.py        # uses ref_1
Writes umrah_voice/narration_en/<id>.wav for every line in umrah_voice/narration_en.json
Already-generated lines are skipped, so you can stop and resume.
"""
import os, re, sys, json
import numpy as np
import soundfile as sf
import torch
from duas_arabic import load, trim
from content import narration_text

REF = f"umrah_voice/ref_{sys.argv[1] if len(sys.argv) > 1 else 1}.wav"
OUT = "umrah_voice/narration_en"
EXAGGERATION = 0.4
CFG_WEIGHT = 0.35
SEEDS = [5, 6, 7]
PAUSE = 0.35


def say(model, sentence):
    letters = sum(ch.isalpha() for ch in sentence)
    best = None
    for seed in SEEDS:
        torch.manual_seed(seed)
        wav = model.generate(sentence, language_id="en", audio_prompt_path=REF,
                             exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
        a = trim(wav.squeeze().detach().cpu().numpy().astype(np.float32), model.sr)
        rate = letters / max(len(a) / model.sr, 0.1)
        score = abs(rate - 12.0)                 # calm narration ~12 letters/s
        if best is None or score < best[0]:
            best = (score, a, rate)
        if 9.0 <= rate <= 15.0:
            break
    return best[1], best[2]


def main():
    lines = narration_text('en')
    os.makedirs(OUT, exist_ok=True)
    model = load()
    sr = model.sr
    gap = np.zeros(int(PAUSE * sr), dtype=np.float32)
    for key, text in lines.items():
        path = f"{OUT}/{key}.wav"
        if os.path.exists(path):
            continue
        sentences = [s.strip() for s in re.findall(r"[^.!?]+[.!?]*", text) if s.strip()]
        parts = []
        for s in sentences:
            a, rate = say(model, s)
            parts += [a, gap]
        out = np.concatenate(parts[:-1])
        out *= 0.89 / (float(np.abs(out).max()) or 1.0)
        sf.write(path, out, sr)
        print(f"{key:20s} {len(out) / sr:5.1f}s")
    print(f"\nDone: {OUT}/")


if __name__ == "__main__":
    main()

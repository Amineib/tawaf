"""Arabic recitation of the Umrah tour duas with Chatterbox Multilingual (voice cloned
from a designed reference made by design_voice_umrah.py).

Run:
  source .venv/bin/activate
  PYTORCH_ENABLE_MPS_FALLBACK=1 python duas_arabic.py            # samples + full set with ref 1
  PYTORCH_ENABLE_MPS_FALLBACK=1 python duas_arabic.py 3          # full set with ref 3

Writes:
  umrah_voice/sample_ref_N.wav   the Talbiyah in each candidate voice (to choose)
  umrah_voice/duas/<key>.wav     one file per dua, in the chosen voice

NOTE: synthetic recitation. Quranic verses (rabbana, maqam, safa_verse) must be checked
by someone qualified in tajweed before release, and ideally replaced by a human reciter.
"""
import os
import sys
import glob
import numpy as np
import soundfile as sf
import torch

REF_DIR = "umrah_voice"
EXAGGERATION = 0.35   # calm, not dramatic
CFG_WEIGHT = 0.3      # slower, steadier pacing
SEEDS = [11, 12, 13]  # first take whose speed looks natural wins
PAUSE = 0.45          # seconds of silence between phrases

TAKBIR = "اللَّهُ أَكْبَرُ، اللَّهُ أَكْبَرُ، اللَّهُ أَكْبَرُ"
DUAS = {
    "niyyah": ["لَبَّيْكَ اللَّهُمَّ عُمْرَةً"],
    "ishtirat": ["اللَّهُمَّ مَحِلِّي حَيْثُ حَبَسْتَنِي"],
    "talbiyah": ["لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ", "لَبَّيْكَ لَا شَرِيكَ لَكَ لَبَّيْكَ",
                 "إِنَّ الْحَمْدَ وَالنِّعْمَةَ لَكَ وَالْمُلْكَ", "لَا شَرِيكَ لَكَ"],
    "enter": ["بِسْمِ اللَّهِ، وَالصَّلَاةُ وَالسَّلَامُ عَلَى رَسُولِ اللَّهِ",
              "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ"],
    "bismillah": ["بِسْمِ اللَّهِ، اللَّهُ أَكْبَرُ"],
    "rabbana": ["رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً", "وَفِي الْآخِرَةِ حَسَنَةً", "وَقِنَا عَذَابَ النَّارِ"],
    "maqam": ["وَاتَّخِذُوا مِن مَّقَامِ إِبْرَاهِيمَ مُصَلًّى"],
    "safa_verse": ["إِنَّ الصَّفَا وَالْمَرْوَةَ مِن شَعَائِرِ اللَّهِ", "أَبْدَأُ بِمَا بَدَأَ اللَّهُ بِهِ"],
    "safa_dhikr": [TAKBIR, "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
                   "لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
                   "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ، أَنْجَزَ وَعْدَهُ",
                   "وَنَصَرَ عَبْدَهُ، وَهَزَمَ الْأَحْزَابَ وَحْدَهُ"],
}


def load():
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    loc = torch.device(device)
    _load = torch.load
    torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": k.get("map_location", loc)})
    try:
        model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
    except TypeError:
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    return model


def trim(a, sr, pad=0.06):
    if not a.size:
        return a
    peak = float(np.abs(a).max()) or 1.0
    loud = np.flatnonzero(np.abs(a) > 0.02 * peak)
    if not loud.size:
        return a
    return a[max(loud[0] - int(pad * sr), 0): min(loud[-1] + int(pad * sr), len(a))]


def say(model, phrase, ref):
    """Generate one phrase; retry seeds if the take is implausibly fast or slow."""
    letters = sum(ch.isalpha() for ch in phrase)
    best = None
    for seed in SEEDS:
        torch.manual_seed(seed)
        wav = model.generate(phrase, language_id="ar", audio_prompt_path=ref,
                             exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
        a = trim(wav.squeeze().detach().cpu().numpy().astype(np.float32), model.sr)
        rate = letters / max(len(a) / model.sr, 0.1)       # letters per second
        score = abs(rate - 9.0)                              # ~9 letters/s = calm recitation pace
        if best is None or score < best[0]:
            best = (score, a, seed, rate)
        if 6.0 <= rate <= 12.0:
            break
    return best[1], best[2], best[3]


def recite(model, lines, ref):
    sr = model.sr
    gap = np.zeros(int(PAUSE * sr), dtype=np.float32)
    parts = []
    for i, line in enumerate(lines):
        a, seed, rate = say(model, line, ref)
        print(f"     phrase {i + 1}: {len(a) / sr:4.1f}s  {rate:4.1f} letters/s  seed {seed}")
        parts += [a, gap]
    out = np.concatenate(parts[:-1])
    peak = float(np.abs(out).max()) or 1.0
    return out * (0.89 / peak)


def main():
    refs = sorted(glob.glob(f"{REF_DIR}/ref_*.wav"))
    if not refs:
        sys.exit("No umrah_voice/ref_*.wav yet: run design_voice_umrah.py first (in .venv-mlx).")
    choice = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    model = load()
    sr = model.sr
    if len(sys.argv) == 1:
        for r in refs:
            n = r.split("_")[-1].split(".")[0]
            print(f"sample with {r}")
            sf.write(f"{REF_DIR}/sample_ref_{n}.wav", recite(model, DUAS["talbiyah"], r), sr)
    ref = f"{REF_DIR}/ref_{choice}.wav"
    os.makedirs(f"{REF_DIR}/duas", exist_ok=True)
    for key, lines in DUAS.items():
        print(f"{key}  (voice {choice})")
        sf.write(f"{REF_DIR}/duas/{key}.wav", recite(model, lines, ref), sr)
    print(f"\nDone: {REF_DIR}/duas/*.wav")


if __name__ == "__main__":
    main()

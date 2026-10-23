"""Canonical lesson and narration text shared with the web players."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_content():
    return json.loads((ROOT / 'web' / 'tour.json').read_text(encoding='utf-8'))


def narration_text(lang, content=None):
    data = content or load_content()
    lines = {f"{station['id']}_{i}": step[lang]
             for station in data['stations'] for i, step in enumerate(station['steps'])}
    if lang == 'en':
        lines.update({f'meaning_{key}': 'Meaning: ' + dua['en'] for key, dua in data['duas'].items()})
    return lines


def dua_phrases(content=None):
    """Split the canonical Arabic text at phrase boundaries for synthetic previews."""
    data = content or load_content()
    return {key: [part.strip() for part in re.split(r'[،—]', dua['ar']) if part.strip()]
            for key, dua in data['duas'].items()}

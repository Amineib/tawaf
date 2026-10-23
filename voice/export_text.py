"""Export TTS input from web/tour.json; --check detects stale checked-in transcripts."""
import argparse
import json
from pathlib import Path
from content import narration_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for lang in ('en', 'ar'):
        target = Path(__file__).with_name(f'narration_{lang}.json')
        lines = narration_text(lang)
        if args.check:
            if json.loads(target.read_text(encoding='utf-8')) != lines:
                raise SystemExit(f'{target.name} is stale; run python voice/export_text.py and review affected recordings')
        else:
            target.write_text(json.dumps(lines, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Narration transcripts match canonical content.' if args.check else 'Narration transcripts exported.')


if __name__ == '__main__':
    main()

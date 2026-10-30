"""Build a ZIP with source, verified outputs and a SHA-256 file manifest."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'runtime', 'verified_runtime', '.git', '.venv', '__pycache__', '.pytest_cache'}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'jharkhand-mini-uddp-pyspark-sqlite.zip')
    args = parser.parse_args()
    files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                   and not set(p.relative_to(ROOT).parts).intersection(EXCLUDED)
                   and p.suffix not in {'.pyc', '.zip'} and p.name != 'FILE_MANIFEST.json')
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT / 'FILE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files + [ROOT / 'FILE_MANIFEST.json']:
            archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
    print(f'{args.output.resolve()} ({len(files) + 1} files)')


if __name__ == '__main__':
    main()

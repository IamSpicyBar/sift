"""Separate prepared inputs from files produced or changed by one execution."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_inputs(output_dir: Path) -> None:
    files = {
        str(p.relative_to(output_dir)): _digest(p)
        for p in output_dir.rglob('*') if p.is_file() and not p.is_symlink()
    }
    context_dir = output_dir.parent / 'input-context'
    if context_dir.exists():
        shutil.rmtree(context_dir)
    for name in files:
        destination = context_dir / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_dir / name, destination)
    (output_dir.parent / 'input-manifest.json').write_text(
        json.dumps({'version': 1, 'files': files}, ensure_ascii=False, indent=2), encoding='utf-8'
    )


def output_files(output_dir: Path):
    manifest_path = output_dir.parent / 'input-manifest.json'
    # Older standalone checker callers have no prepared-input manifest.
    inputs = json.loads(manifest_path.read_text(encoding='utf-8'))['files'] if manifest_path.exists() else {}
    for path in sorted(output_dir.rglob('*')):
        if not path.is_file() or path.is_symlink() or any(p.startswith('.') for p in path.relative_to(output_dir).parts):
            continue
        relative = str(path.relative_to(output_dir))
        if inputs.get(relative) != _digest(path):
            yield path


MAX_JUDGE_CHARACTERS = 128000


class EvidenceUnavailable(ValueError):
    """Evidence is missing, binary, changed, or exceeds the judge budget."""


def check_judge_budget(text: str) -> str:
    if len(text) > MAX_JUDGE_CHARACTERS:
        raise EvidenceUnavailable(f"Evidence exceeds judge budget ({MAX_JUDGE_CHARACTERS} characters); not silently truncated")
    return text


def read_evidence_text(path: Path) -> str:
    if path.stat().st_size > MAX_JUDGE_CHARACTERS * 4:
        raise EvidenceUnavailable(f"Evidence file too large: {path.name}")
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        raise EvidenceUnavailable(f"Binary evidence requires another judge: {path.name}") from exc
    if '\0' in text:
        raise EvidenceUnavailable(f"Binary evidence requires another judge: {path.name}")
    return check_judge_budget(text)


def input_context(output_dir: Path) -> str:
    manifest = output_dir.parent / 'input-manifest.json'
    if not manifest.exists():
        return ''
    inputs = json.loads(manifest.read_text(encoding='utf-8'))['files']
    parts = []
    for name, expected in inputs.items():
        path = output_dir.parent / 'input-context' / name
        if not path.is_file() or _digest(path) != expected:
            raise EvidenceUnavailable(f"Original input context unavailable: {name}")
        parts.append(f"=== {name} (supplied before execution; NOT an answer) ===\n" + read_evidence_text(path))
    return check_judge_budget('\n\n'.join(parts))

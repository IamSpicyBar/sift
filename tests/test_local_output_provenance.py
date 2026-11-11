import json
from pathlib import Path

from sift.execution.comparison_suite import _collect_run_output
from sift.scoring.client import ScoringClient
from sift.scoring.programmatic import ProgrammaticChecker


def test_scoring_respects_selected_transport(monkeypatch):
    captured = {}
    monkeypatch.setenv('SIFT_LLM_TRANSPORT', 'dsh')
    def complete(prompt, **kwargs):
        captured.update(kwargs)
        return '{}'
    monkeypatch.setattr('sift.scoring.client.call_llm_with_retry', complete)
    assert ScoringClient().complete('request') == '{}'
    assert captured['transport'] == 'dsh'


def test_unchanged_inputs_are_not_outputs(tmp_path):
    import hashlib
    output = tmp_path / 'outputs'
    output.mkdir()
    reference = output / 'reference.md'
    reference.write_text('INPUT_SENTINEL')
    (tmp_path / 'input-manifest.json').write_text(json.dumps({
        'version': 1, 'files': {'reference.md': hashlib.sha256(reference.read_bytes()).hexdigest()}
    }))
    verdict, _ = ProgrammaticChecker._contains_pattern({'pattern': 'INPUT_SENTINEL'}, output, {'transcript': 'actual answer'})
    assert verdict.value == 'FAIL'
    reference.write_text('OUTPUT_SENTINEL')
    verdict, _ = ProgrammaticChecker._contains_pattern({'pattern': 'OUTPUT_SENTINEL'}, output, {})
    assert verdict.value == 'PASS'


def test_comparison_uses_full_answer_and_changed_artifacts(tmp_path):
    import hashlib
    output = tmp_path / 'outputs'
    output.mkdir()
    reference = output / 'reference.md'
    reference.write_text('INPUT_SENTINEL')
    (tmp_path / 'input-manifest.json').write_text(json.dumps({
        'version': 1, 'files': {'reference.md': hashlib.sha256(reference.read_bytes()).hexdigest()}
    }))
    answer = 'actual answer ' * 800 + 'END_OF_FULL_ANSWER'
    (tmp_path / 'answer.txt').write_text(answer)
    (output / 'result.md').write_text('GENERATED_ARTIFACT')
    collected = _collect_run_output(tmp_path)
    assert answer in collected
    assert 'GENERATED_ARTIFACT' in collected
    assert 'INPUT_SENTINEL' not in collected


def test_grading_is_not_an_answer_fallback(tmp_path):
    (tmp_path / 'grading.json').write_text('{"summary": "not an answer"}')
    assert _collect_run_output(tmp_path) == ''

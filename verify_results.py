"""Offline verification of the published study. Does not call an API."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    successful = answers = failures = input_tokens = output_tokens = 0
    for manifest_path in sorted((ROOT / 'results').glob('*/manifest.json')):
        directory = manifest_path.parent
        manifest = json.loads(manifest_path.read_text())
        rows = [json.loads(line) for line in (directory / 'results.jsonl').read_text().splitlines()]
        assert len({r['trial'] for r in rows}) == len(rows), directory
        if 'cases' in manifest:
            cases = {c['id']: c for c in manifest['cases']}
            schedule = json.loads((directory / 'schedule.json').read_text())
            assert len(rows) == len(schedule) == sum(c['repetitions'] for c in cases.values())
            counts = Counter(r['case_id'] for r in rows)
            assert all(counts[k] == c['repetitions'] for k, c in cases.items())
        else:
            cases = None
        for row in rows:
            if cases is not None:
                case = cases[row['case_id']]
                payload = case['payload']
                expected = case['expected']
                assert schedule[row['trial'] - 1] == [row['case_id'], row['repetition']]
            else:
                payload = manifest['payload']
                expected = manifest.get('expected')
            assert row['payload_sha256'] == hashlib.sha256(json.dumps(payload).encode()).hexdigest()
            if 'error' in row:
                failures += 1
                continue
            raw = json.loads(row['raw_response'])
            assert raw == row['response']
            assert row['http_status'] == 200
            assert raw['model'] == 'jev-1.13.0'
            assert set(raw['answers']) == set(payload['questions'])
            for name, answer in raw['answers'].items():
                assert answer['type'] == 'choice'
                assert answer['choice'] in payload['questions'][name]['criteria']
                answers += 1
            if expected is not None:
                all_correct = all(raw['answers'][name]['choice'] == label for name, label in expected.items())
                assert row['all_correct'] == all_correct
            successful += 1
            input_tokens += raw['usage']['input_tokens']
            output_tokens += raw['usage']['output_tokens']
    assert (successful, answers, failures) == (7805, 9280, 2)
    assert (input_tokens, output_tokens) == (5036368, 420305)
    print(f'Verified {successful:,} successful requests, {answers:,} answers, and {failures} failed startup attempts.')
    print(f'Reported usage: {input_tokens:,} input tokens; {output_tokens:,} output tokens.')


if __name__ == '__main__':
    main()
